"""HTTPS LAN guard and secure-cookie integration test for MaClasse V25."""
import json, os, shutil, socket, ssl, subprocess, sys, tempfile, time, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timedelta, timezone
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

SOURCE=Path(__file__).resolve().parents[1]

def request(url, method='GET', payload=None, origin=None, context=None, cookie=None, host_header=None):
    headers={}
    body=None
    if payload is not None:
        headers['Content-Type']='application/json'
        body=json.dumps(payload).encode()
    if origin is not None:
        headers['Origin']=origin
    if cookie is not None:
        headers['Cookie']=cookie
    if host_header is not None:
        headers['Host']=host_header
    req=urllib.request.Request(url,data=body,headers=headers,method=method)
    opener=urllib.request.build_opener(urllib.request.HTTPSHandler(context=context)) if context else urllib.request.build_opener()
    try:
        with opener.open(req,timeout=4) as response:
            return response.status,response.headers,response.read()
    except urllib.error.HTTPError as error:
        return error.code,error.headers,error.read()


def create_dns_certificate(certificate_path, key_path, hostname):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, hostname)
    ])
    now = datetime.now(timezone.utc)
    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before((now - timedelta(days=1)).replace(tzinfo=None))
        .not_valid_after((now + timedelta(days=30)).replace(tzinfo=None))
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName(hostname)]),
            critical=False,
        )
        .sign(private_key, hashes.SHA256())
    )
    certificate_path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ))
    key_path.chmod(0o600)


def run_public_dns_hostname_mode():
    temporary = Path(tempfile.mkdtemp(prefix='maclasse-v25-public-tls-'))
    app = temporary / 'app'
    shutil.copytree(SOURCE, app)
    certificate = temporary / 'fullchain.pem'
    private_key = temporary / 'privkey.pem'
    hostname = 'maclasse.example.test'
    create_dns_certificate(certificate, private_key, hostname)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    url = f'https://127.0.0.1:{port}'
    dns_host = f'{hostname}:{port}'
    env = os.environ.copy()
    env.update({
        'MACLASSE_HOST': '127.0.0.1',
        'MACLASSE_PORT': str(port),
        'MACLASSE_TLS_CERT': str(certificate),
        'MACLASSE_TLS_KEY': str(private_key),
        'MACLASSE_TLS_HOSTNAME': hostname,
    })
    process = subprocess.Popen(
        ['python3', 'server.py'], cwd=app, env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    context = ssl._create_unverified_context()
    try:
        ready = False
        for _ in range(60):
            try:
                status, _, _ = request(
                    url + '/api/auth/setup-status',
                    context=context,
                    host_header=dns_host,
                )
                if status == 200:
                    ready = True
                    break
            except Exception:
                time.sleep(0.1)
        assert ready, 'TLS listener did not accept the configured DNS Host.'

        status, _, body = request(
            url + '/api/auth/setup',
            method='POST',
            payload={
                'first': 'Test', 'last': 'DNS',
                'username': 'dns-admin',
                'password': 'MotDePasseDNSLongEtSolide!',
            },
            origin=f'https://{dns_host}',
            context=context,
            host_header=dns_host,
        )
        assert status == 201, body.decode('utf-8', 'replace')

        attacker = f'attacker.example.test:{port}'
        status, _, _ = request(
            url + '/api/auth/login',
            method='POST',
            payload={'username': 'dns-admin', 'password': 'MotDePasseDNSLongEtSolide!'},
            origin=f'https://{attacker}',
            context=context,
            host_header=attacker,
        )
        assert status == 403, 'Un Host/Origin DNS non configuré doit être refusé.'
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        shutil.rmtree(temporary, ignore_errors=True)
    print('OK — TLS avec nom DNS explicite, Host/Origin autorisés et DNS rebinding arbitraire refusé.')


def run():
    if shutil.which('openssl') is None:
        raise RuntimeError('OpenSSL is required for this TLS integration test.')
    temp=Path(tempfile.mkdtemp(prefix='maclasse-v25-tls-'))
    app=temp/'app'
    shutil.copytree(SOURCE,app)
    setup_env=os.environ.copy(); setup_env['PYTHON']=sys.executable
    subprocess.run(['bash',str(app/'Configurer-MaClasse-Reseau.sh'),'192.168.1.20'],cwd=app,env=setup_env,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    cert=app/'data'/'tls'/'server.crt'; key=app/'data'/'tls'/'server.key'
    ca=app/'data'/'tls'/'ca.crt'
    subprocess.run(['openssl','verify','-CAfile',str(ca),str(cert)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0)); port=sock.getsockname()[1]
    host=f'127.0.0.1:{port}'
    base=f'https://{host}'
    env=os.environ.copy()
    env.update({'MACLASSE_HOST':'127.0.0.1','MACLASSE_PORT':str(port),'MACLASSE_TLS_CERT':str(cert),'MACLASSE_TLS_KEY':str(key)})
    process=subprocess.Popen(['python3','server.py'],cwd=app,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    context=ssl._create_unverified_context()
    try:
        ready=False
        for _ in range(50):
            try:
                status,_,_=request(base+'/api/auth/setup-status',context=context)
                if status==200: ready=True; break
            except Exception:
                time.sleep(.1)
        assert ready, 'TLS server did not start'
        password='motDePasseDirectionTresFort!'
        status,headers,body=request(base+'/api/auth/setup','POST',{'first':'Camille','last':'Durand','username':'direction','password':password},origin=base,context=context)
        assert status==201
        cookie=headers.get('Set-Cookie','')
        assert 'HttpOnly' in cookie and 'SameSite=Strict' in cookie and 'Secure' in cookie
        assert headers.get('Strict-Transport-Security')=='max-age=31536000'
        status,_,_=request(base+'/api/auth/login','POST',{'username':'direction','password':password},origin=f'http://{host}',context=context)
        assert status==403, 'An HTTP Origin must not be accepted on the HTTPS listener'
        # Vérifie qu'un poste client HTTPS du réseau peut réellement télécharger
        # un bulletin PDF depuis le serveur (et pas seulement ouvrir une session).
        database_path=app/'data'/'maclasse.json'
        database=json.loads(database_path.read_text(encoding='utf-8'))
        database.setdefault('classes',[]).append({'id':'network-class','name':'6A','teacherIds':[]})
        database.setdefault('students',[]).append({'id':'network-student','classId':'network-class','first':'Alice','last':'Martin'})
        database.setdefault('settings',{}).setdefault('terms',[]).append({'id':'network-term','name':'Trimestre 1','start':'2026-09-01','end':'2026-12-31'})
        database.setdefault('evaluations',[])
        database.setdefault('attendance',[])
        database.setdefault('schedule',[])
        database.setdefault('bulletins',[]).append({'id':'network-bulletin','studentId':'network-student','classId':'network-class','termId':'network-term','validated':True,'published':True,'publishedAt':'2026-11-17T10:00:00Z','overall':'Bon travail','subjectData':{}})
        database_path.write_text(json.dumps(database,ensure_ascii=False),encoding='utf-8')
        status,pdf_headers,pdf_body=request(base+'/api/bulletin-pdf','POST',{'bulletinId':'network-bulletin'},origin=base,context=context,cookie=cookie.split(';')[0])
        assert status==200, 'A remote HTTPS client must be able to generate a published bulletin PDF: '+pdf_body.decode('utf-8','replace')[:300]
        assert 'application/pdf' in pdf_headers.get('Content-Type','').lower()
        assert pdf_body.startswith(b'%PDF-'), 'The remote endpoint must return actual PDF bytes'
        status,logout_headers,_=request(base+'/api/auth/logout','POST',{},origin=base,context=context,cookie=cookie.split(';')[0])
        assert status==200 and 'Secure' in logout_headers.get('Set-Cookie','')
    finally:
        process.terminate()
        process.wait(timeout=5)
        shutil.rmtree(temp,ignore_errors=True)

    # Un hôte privé ne doit jamais démarrer en HTTP, même avec le mode LAN explicite.
    with tempfile.TemporaryDirectory(prefix='maclasse-v25-lan-guard-') as cwd:
        guard_app=Path(cwd)/'app'; shutil.copytree(SOURCE,guard_app)
        env=os.environ.copy()
        env.update({'MACLASSE_HOST':'192.168.1.20','MACLASSE_PORT':'8765','MACLASSE_LAN_MODE':'1'})
        env.pop('MACLASSE_TLS_CERT',None); env.pop('MACLASSE_TLS_KEY',None)
        result=subprocess.run(['python3','server.py'],cwd=guard_app,env=env,text=True,capture_output=True,timeout=5)
        assert result.returncode==2 and 'exige HTTPS' in result.stdout+result.stderr
    print('OK — TLS serveur, cookie Secure, origine HTTPS stricte et refus du LAN en HTTP.')
    run_public_dns_hostname_mode()

if __name__=='__main__':
    run()
