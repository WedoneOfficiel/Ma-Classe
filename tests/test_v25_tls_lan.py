"""HTTPS LAN guard and secure-cookie integration test for MaClasse V25."""
import json, os, shutil, socket, ssl, subprocess, sys, tempfile, time, urllib.request, urllib.error
from pathlib import Path

SOURCE=Path(__file__).resolve().parents[1]

def request(url, method='GET', payload=None, origin=None, context=None):
    headers={}
    body=None
    if payload is not None:
        headers['Content-Type']='application/json'
        body=json.dumps(payload).encode()
    if origin is not None:
        headers['Origin']=origin
    req=urllib.request.Request(url,data=body,headers=headers,method=method)
    opener=urllib.request.build_opener(urllib.request.HTTPSHandler(context=context)) if context else urllib.request.build_opener()
    try:
        with opener.open(req,timeout=4) as response:
            return response.status,response.headers,response.read()
    except urllib.error.HTTPError as error:
        return error.code,error.headers,error.read()

def run():
    if shutil.which('openssl') is None:
        raise RuntimeError('OpenSSL is required for this TLS integration test.')
    temp=Path(tempfile.mkdtemp(prefix='maclasse-v25-tls-'))
    app=temp/'app'
    shutil.copytree(SOURCE,app)
    setup_env=os.environ.copy(); setup_env['PYTHON']=sys.executable
    subprocess.run(['bash',str(app/'Configurer-MaClasse-Reseau.sh'),'127.0.0.1'],cwd=app,env=setup_env,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
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
        status,_,_=request(base+'/api/auth/login','POST',{'username':'direction','password':password},origin=f'http://{host}',context=context)
        assert status==403, 'An HTTP Origin must not be accepted on the HTTPS listener'
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

if __name__=='__main__':
    run()
