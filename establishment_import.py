"""Import sûr d'une configuration complète d'établissement MaClasse.

Le module est indépendant du serveur HTTP afin que ses validations métier soient
testables sans démarrer le serveur ni modifier une base réelle.
"""
from __future__ import annotations

import copy
import datetime as _dt
import re
import unicodedata
from collections import defaultdict

FORMAT_NAME = "maclasse-establishment"
FORMAT_VERSION = 1

LIMITS = {
    "classes": 300,
    "students": 20000,
    "teachers": 3000,
    "rooms": 2000,
    "schedule": 50000,
}
DAY_NAMES = {
    "monday": 0, "lundi": 0,
    "tuesday": 1, "mardi": 1,
    "wednesday": 2, "mercredi": 2,
    "thursday": 3, "jeudi": 3,
    "friday": 4, "vendredi": 4,
    "saturday": 5, "samedi": 5,
    "sunday": 6, "dimanche": 6,
}
KEY_RE = re.compile(r"^[A-Za-z0-9._:-]{1,60}$")
USERNAME_RE = re.compile(r"^[a-z0-9._-]{3,40}$")
TIME_RE = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _text(value, label, errors, *, required=False, maximum=160):
    if value is None:
        value = ""
    if not isinstance(value, str):
        errors.append(f"{label} doit être une chaîne de caractères.")
        return ""
    value = value.strip()
    if required and not value:
        errors.append(f"{label} est obligatoire.")
    if len(value) > maximum:
        errors.append(f"{label} dépasse {maximum} caractères.")
    if any(ord(ch) < 32 and ch not in "\t" for ch in value):
        errors.append(f"{label} contient un caractère de contrôle interdit.")
    return value


def _key(value, label, errors, *, required=True):
    value = _text(value, label, errors, required=required, maximum=60)
    if value and not KEY_RE.fullmatch(value):
        errors.append(f"{label} doit utiliser uniquement lettres, chiffres, point, tiret, deux-points ou underscore.")
    return value


def _check_fields(record, allowed, label, errors):
    if not isinstance(record, dict):
        return
    unknown = sorted(set(record) - set(allowed))
    for field in unknown:
        errors.append(f"{label} : propriété inconnue {field!r}. Vérifie le schéma Ma Classe.")


def _unique_records(records, kind, errors, allowed_fields):
    result = {}
    if not isinstance(records, list):
        errors.append(f"La rubrique {kind} doit être une liste.")
        return result
    if len(records) > LIMITS[kind]:
        errors.append(f"La rubrique {kind} dépasse la limite de {LIMITS[kind]} éléments.")
        return result
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"{kind}[{index}] doit être un objet JSON.")
            continue
        _check_fields(record, allowed_fields, f"{kind}[{index}]", errors)
        key = _key(record.get("key"), f"{kind}[{index}].key", errors)
        if key:
            if key in result:
                errors.append(f"Clé {key!r} utilisée plusieurs fois dans {kind}.")
            else:
                result[key] = record
    return result


def _string_list(value, label, errors, *, maximum_items=100, item_maximum=100):
    if value is None:
        return []
    if not isinstance(value, list):
        errors.append(f"{label} doit être une liste.")
        return []
    if len(value) > maximum_items:
        errors.append(f"{label} contient plus de {maximum_items} éléments.")
        return []
    result = []
    seen = set()
    for item in value:
        item = _text(item, label, errors, required=True, maximum=item_maximum)
        folded = item.casefold()
        if item and folded not in seen:
            result.append(item)
            seen.add(folded)
    return result


def _key_list(value, label, errors, *, maximum_items=500):
    if value is None:
        return []
    if not isinstance(value, list):
        errors.append(f"{label} doit être une liste de clés.")
        return []
    if len(value) > maximum_items:
        errors.append(f"{label} contient plus de {maximum_items} éléments.")
        return []
    result = []
    seen = set()
    for item in value:
        key = _key(item, label, errors)
        if key and key not in seen:
            result.append(key)
            seen.add(key)
    return result


def _date(value, label, errors, *, required=False):
    value = _text(value, label, errors, required=required, maximum=10)
    if not value:
        return None
    if not DATE_RE.fullmatch(value):
        errors.append(f"{label} doit être au format AAAA-MM-JJ.")
        return None
    try:
        return _dt.date.fromisoformat(value)
    except ValueError:
        errors.append(f"{label} n'est pas une date valide.")
        return None


def _time(value, label, errors):
    value = _text(value, label, errors, required=True, maximum=5)
    if not TIME_RE.fullmatch(value):
        errors.append(f"{label} doit être au format HH:MM.")
        return None
    hour, minute = map(int, value.split(":"))
    return hour * 60 + minute


def _day(value, label, errors):
    if isinstance(value, bool):
        errors.append(f"{label} doit être un jour ouvré (lundi à vendredi).")
        return None
    if isinstance(value, int):
        day = value
    elif isinstance(value, str):
        day = DAY_NAMES.get(value.strip().casefold())
    else:
        day = None
    if day is None or day < 0 or day > 4:
        errors.append(f"{label} doit désigner un jour ouvré (lundi à vendredi).")
        return None
    return day


def _period_weeks(record):
    recurrence = record.get("recurrence", "weekly")
    if recurrence == "once":
        return 0
    if recurrence == "biweekly":
        return 2
    if recurrence == "triweekly":
        return 3
    if recurrence == "custom":
        return int(record.get("intervalWeeks", 4))
    return 1


def _first_occurrence(record):
    start = record["startDate"]
    day = record["day"]
    offset = (day - start.weekday()) % 7
    return start + _dt.timedelta(days=offset)


def _occurs(record, date):
    first = _first_occurrence(record)
    if date < first:
        return False
    if record.get("endDate") and date > record["endDate"]:
        return False
    if date.isoformat() in record.get("exceptions", []):
        return False
    if record.get("recurrence", "weekly") == "once":
        return date == first
    return date.weekday() == record["day"] and ((date - first).days // 7) % _period_weeks(record) == 0


def _recurrences_overlap(left, right):
    if left["day"] != right["day"]:
        return False
    first = max(_first_occurrence(left), _first_occurrence(right))
    ends = [x.get("endDate") or (x["startDate"] + _dt.timedelta(days=365 * 5)) for x in (left, right)]
    last = min(ends)
    if first > last:
        return False
    periods = [_period_weeks(left), _period_weeks(right)]
    if 0 in periods:
        candidates = [_first_occurrence(left)] if periods[0] == 0 else [_first_occurrence(right)]
        return any(first <= candidate <= last and _occurs(left, candidate) and _occurs(right, candidate) for candidate in candidates)
    # The joint recurrence repeats after the least common multiple of both periods.
    import math
    cycle = math.lcm(periods[0], periods[1])
    exceptions = len(set(left.get("exceptions", [])) | set(right.get("exceptions", [])))
    limit = min(last, first + _dt.timedelta(weeks=cycle + exceptions + 1))
    date = first
    while date <= limit:
        if _occurs(left, date) and _occurs(right, date):
            return True
        date += _dt.timedelta(days=7)
    return False


def _groups_overlap(left, right):
    return not left or not right or left == right


def _overlap_time(left, right):
    return left["startMinutes"] < right["endMinutes"] and right["startMinutes"] < left["endMinutes"]


def _iter_resource_overlap_pairs(lessons):
    """Yield only overlapping lesson pairs that share a class, teacher, or room.

    Resource buckets and a per-day interval sweep avoid the previous global
    O(n²) scan when a large schedule contains mostly unrelated resources.
    """
    resources = defaultdict(list)
    for index, lesson in enumerate(lessons):
        for class_key in lesson["classes"]:
            resources[("class", class_key)].append(index)
        for teacher_key in lesson["teachers"]:
            resources[("teacher", teacher_key)].append(index)
        if lesson["room"]:
            resources[("room", lesson["room"])].append(index)

    seen = set()
    for (resource_type, _resource_key), indices in resources.items():
        by_day = defaultdict(list)
        for index in indices:
            by_day[lessons[index]["day"]].append(index)
        for day_indices in by_day.values():
            day_indices.sort(
                key=lambda index: (
                    lessons[index]["startMinutes"],
                    lessons[index]["endMinutes"],
                )
            )
            if resource_type != "class":
                active = []
                for current_index in day_indices:
                    current = lessons[current_index]
                    active = [
                        previous_index for previous_index in active
                        if lessons[previous_index]["endMinutes"] > current["startMinutes"]
                    ]
                    for previous_index in active:
                        pair = (min(previous_index, current_index), max(previous_index, current_index))
                        if pair not in seen:
                            seen.add(pair)
                            yield pair
                    active.append(current_index)
                continue

            # Les cours de groupes différents sont indépendants. Conserver
            # séparément les créneaux de classe entière et ceux de chaque groupe
            # évite de comparer toutes les paires entre groupes parallèles.
            active_whole_class = []
            active_by_group = defaultdict(list)
            for current_index in day_indices:
                current = lessons[current_index]
                active_whole_class = [
                    previous_index for previous_index in active_whole_class
                    if lessons[previous_index]["endMinutes"] > current["startMinutes"]
                ]
                if current["group"]:
                    group_active = [
                        previous_index for previous_index in active_by_group[current["group"]]
                        if lessons[previous_index]["endMinutes"] > current["startMinutes"]
                    ]
                    active_by_group[current["group"]] = group_active
                    previous_indices = active_whole_class + group_active
                else:
                    previous_indices = list(active_whole_class)
                    for group, group_indices in list(active_by_group.items()):
                        remaining = [
                            previous_index for previous_index in group_indices
                            if lessons[previous_index]["endMinutes"] > current["startMinutes"]
                        ]
                        if remaining:
                            active_by_group[group] = remaining
                            previous_indices.extend(remaining)
                        else:
                            del active_by_group[group]

                for previous_index in previous_indices:
                    pair = (min(previous_index, current_index), max(previous_index, current_index))
                    if pair not in seen:
                        seen.add(pair)
                        yield pair

                if current["group"]:
                    active_by_group[current["group"]].append(current_index)
                else:
                    active_whole_class.append(current_index)


def _username_base(teacher):
    raw = unicodedata.normalize("NFKD", f"{teacher.get('first', '')}.{teacher.get('last', '')}")
    ascii_name = raw.encode("ascii", "ignore").decode("ascii").lower()
    base = re.sub(r"[^a-z0-9._-]+", ".", ascii_name).strip("._-")
    return (base or "professeur")[:32]


def validate_bundle(bundle, existing_data=None):
    """Validate and normalize an imported establishment bundle; never mutates input."""
    errors, warnings = [], []
    existing_data = existing_data if isinstance(existing_data, dict) else {}
    if not isinstance(bundle, dict):
        return {"errors": ["Le fichier doit contenir un objet JSON."], "warnings": [], "summary": {}, "quality": {}}
    _check_fields(bundle, {"format", "version", "createTeacherAccounts", "createStudentProfiles", "establishment", "classes", "teachers", "students", "rooms", "schedule"}, "Racine", errors)
    for required in ("format", "version", "establishment", "classes", "teachers", "students", "rooms", "schedule"):
        if required not in bundle:
            errors.append(f"Propriété obligatoire manquante : {required}.")
    if bundle.get("format") != FORMAT_NAME:
        errors.append(f"Format incorrect : format attendu {FORMAT_NAME!r}.")
    if isinstance(bundle.get("version"), bool) or not isinstance(bundle.get("version"), int) or bundle.get("version") != FORMAT_VERSION:
        errors.append(f"Version de format non prise en charge : version {FORMAT_VERSION} attendue.")
    create_teacher_accounts = bundle.get("createTeacherAccounts", True)
    if not isinstance(create_teacher_accounts, bool):
        errors.append("createTeacherAccounts doit être un booléen (true ou false).")
        create_teacher_accounts = True
    create_student_profiles = bundle.get("createStudentProfiles", True)
    if not isinstance(create_student_profiles, bool):
        errors.append("createStudentProfiles doit être un booléen (true ou false).")
        create_student_profiles = True
    establishment = bundle.get("establishment", {})
    if not isinstance(establishment, dict):
        errors.append("establishment doit être un objet.")
        establishment = {}
    _check_fields(establishment, {"name"}, "establishment", errors)
    establishment_name = _text(establishment.get("name", ""), "Nom de l'établissement", errors, maximum=120)

    classes_raw = bundle.get("classes", [])
    teachers_raw = bundle.get("teachers", [])
    students_raw = bundle.get("students", [])
    rooms_raw = bundle.get("rooms", [])
    schedule_raw = bundle.get("schedule", [])
    class_records = _unique_records(classes_raw, "classes", errors, {"key", "name", "levels", "groups", "attendanceMode", "periodMode", "principalTeacher", "teachers", "subjectRequirements", "expectedStudentCount"})
    teacher_records = _unique_records(teachers_raw, "teachers", errors, {"key", "first", "last", "email", "phone", "profileNotes", "subjects", "classes", "username", "unavailable"})
    student_records = _unique_records(students_raw, "students", errors, {"key", "first", "last", "class", "level", "group", "birth", "sex", "email", "phone", "notes"})
    if not create_student_profiles and student_records:
        errors.append("createStudentProfiles=false : students doit être une liste vide ; les identités seront ajoutées plus tard dans Ma Classe.")
    room_records = _unique_records(rooms_raw, "rooms", errors, {"key", "name", "type", "capacity", "equipment", "unavailable"})
    schedule_records = _unique_records(schedule_raw, "schedule", errors, {"key", "classes", "class", "day", "start", "end", "subject", "group", "teachers", "teacher", "room", "recurrence", "intervalWeeks", "startDate", "endDate", "exceptions", "equipment"})

    classes, teachers, students, rooms, schedule = {}, {}, {}, {}, {}
    for key, raw in class_records.items():
        name = _text(raw.get("name"), f"classes[{key}].name", errors, required=True, maximum=100)
        levels = _string_list(raw.get("levels"), f"classes[{key}].levels", errors, maximum_items=8, item_maximum=40)
        if not levels:
            errors.append(f"La classe {name or key} doit comporter au moins un niveau.")
        groups = _string_list(raw.get("groups"), f"classes[{key}].groups", errors, maximum_items=100, item_maximum=80)
        attendance_mode = raw.get("attendanceMode", "hour")
        period_mode = raw.get("periodMode", "trimestres")
        if attendance_mode not in ("hour", "halfday"):
            errors.append(f"La classe {name or key} : attendanceMode doit être 'hour' ou 'halfday'.")
            attendance_mode = "hour"
        if period_mode not in ("trimestres", "semestres"):
            errors.append(f"La classe {name or key} : periodMode doit être 'trimestres' ou 'semestres'.")
            period_mode = "trimestres"
        principal = _key(raw.get("principalTeacher", ""), f"Classe {key} : principalTeacher", errors, required=False)
        teacher_keys = _key_list(raw.get("teachers", []), f"Classe {key} : teachers", errors)
        requirements = raw.get("subjectRequirements", [])
        clean_requirements = []
        if not isinstance(requirements, list):
            errors.append(f"Classe {key} : subjectRequirements doit être une liste.")
        else:
            for index, req in enumerate(requirements):
                if not isinstance(req, dict):
                    errors.append(f"Classe {key} : subjectRequirements[{index}] doit être un objet.")
                    continue
                _check_fields(req, {"subject", "hoursPerWeek", "group"}, f"Classe {key} : subjectRequirements[{index}]", errors)
                subject = _text(req.get("subject"), f"Classe {key} : matière requise", errors, required=True, maximum=80)
                try:
                    raw_hours = req.get("hoursPerWeek")
                    if isinstance(raw_hours, bool) or not isinstance(raw_hours, (int, float)):
                        raise ValueError()
                    hours = float(raw_hours)
                    if not (0 < hours <= 40):
                        raise ValueError()
                except (TypeError, ValueError):
                    errors.append(f"Classe {key} : hoursPerWeek doit être compris entre 0 et 40.")
                    hours = 0
                group = _text(req.get("group", ""), f"Classe {key} : groupe de matière", errors, maximum=80)
                clean_requirements.append({"subject": subject, "hoursPerWeek": hours, "group": group})
        expected_count = raw.get("expectedStudentCount")
        if expected_count is not None and (isinstance(expected_count, bool) or not isinstance(expected_count, int) or expected_count < 0 or expected_count > 1000):
            errors.append(f"Classe {key} : expectedStudentCount doit être un entier de 0 à 1000.")
            expected_count = None
        classes[key] = {
            "key": key, "name": name, "levels": levels, "groups": groups,
            "attendanceMode": attendance_mode, "periodMode": period_mode,
            "principalTeacher": principal, "teachers": teacher_keys,
            "subjectRequirements": clean_requirements, "expectedStudentCount": expected_count,
        }

    for key, raw in teacher_records.items():
        first = _text(raw.get("first"), f"teachers[{key}].first", errors, required=True, maximum=80)
        last = _text(raw.get("last"), f"teachers[{key}].last", errors, required=True, maximum=80)
        email = _text(raw.get("email", ""), f"teachers[{key}].email", errors, maximum=254)
        phone = _text(raw.get("phone", ""), f"teachers[{key}].phone", errors, maximum=40)
        notes = _text(raw.get("profileNotes", ""), f"teachers[{key}].profileNotes", errors, maximum=4000)
        subjects = _string_list(raw.get("subjects", []), f"teachers[{key}].subjects", errors, maximum_items=80, item_maximum=80)
        class_keys = _key_list(raw.get("classes", []), f"teachers[{key}].classes", errors)
        username = _text(raw.get("username", ""), f"teachers[{key}].username", errors, maximum=40).lower()
        if username and not USERNAME_RE.fullmatch(username):
            errors.append(f"Professeur {key} : username doit contenir 3 à 40 caractères minuscules, chiffres, point, tiret ou underscore.")
        unavailable = raw.get("unavailable", [])
        if not isinstance(unavailable, list) or len(unavailable) > 500:
            errors.append(f"Professeur {key} : unavailable doit être une liste de 500 indisponibilités maximum.")
            unavailable = []
        clean_unavailable = []
        for index, slot in enumerate(unavailable):
            if not isinstance(slot, dict):
                errors.append(f"Professeur {key} : unavailable[{index}] doit être un objet.")
                continue
            _check_fields(slot, {"day", "start", "end"}, f"Professeur {key} : unavailable[{index}]", errors)
            day = _day(slot.get("day"), f"Professeur {key} : jour indisponible", errors)
            start = _time(slot.get("start"), f"Professeur {key} : début indisponible", errors)
            end = _time(slot.get("end"), f"Professeur {key} : fin indisponible", errors)
            if start is not None and end is not None and start >= end:
                errors.append(f"Professeur {key} : une indisponibilité doit finir après son début.")
            clean_unavailable.append({"day": day, "startMinutes": start, "endMinutes": end})
        teachers[key] = {
            "key": key, "first": first, "last": last, "email": email, "phone": phone,
            "profileNotes": notes, "subjects": subjects, "classes": class_keys,
            "username": username, "unavailable": clean_unavailable,
        }

    existing_classes = {
        str(x.get("name", "")).strip().casefold()
        for x in existing_data.get("classes", []) if isinstance(x, dict)
    }
    settings = existing_data.get("settings", {})
    if not isinstance(settings, dict):
        settings = {}
    existing_rooms = {
        str(x.get("name", "")).strip().casefold()
        for x in settings.get("rooms", []) if isinstance(x, dict)
    }
    incoming_class_names = set()
    for key, record in classes.items():
        normalized_name = record["name"].casefold()
        if normalized_name in existing_classes:
            errors.append(f"La classe {record['name']!r} existe déjà dans Ma Classe.")
        if normalized_name in incoming_class_names:
            errors.append(f"Le nom de classe {record['name']!r} est utilisé plusieurs fois dans le dossier.")
        incoming_class_names.add(normalized_name)
        if record["principalTeacher"] and record["principalTeacher"] not in teachers:
            errors.append(f"Classe {key} : professeur principal {record['principalTeacher']!r} introuvable.")
        for teacher_key in record["teachers"]:
            if teacher_key not in teachers:
                errors.append(f"Classe {key} : professeur {teacher_key!r} introuvable.")

    for key, record in teachers.items():
        for class_key in record["classes"]:
            if class_key not in classes:
                errors.append(f"Professeur {key} : classe {class_key!r} introuvable.")
    existing_usernames = {
        str(x.get("username", "")).casefold()
        for x in existing_data.get("users", []) if isinstance(x, dict)
    }
    requested_usernames = set()
    for key, record in teachers.items():
        username = record["username"]
        if username:
            if username in existing_usernames or username in requested_usernames:
                errors.append(f"Identifiant professeur {username!r} déjà utilisé.")
            requested_usernames.add(username)

    incoming_room_names = set()
    for key, raw in room_records.items():
        name = _text(raw.get("name"), f"rooms[{key}].name", errors, required=True, maximum=100)
        kind = _text(raw.get("type", "classroom"), f"rooms[{key}].type", errors, maximum=40)
        try:
            raw_capacity = raw.get("capacity", 0)
            if isinstance(raw_capacity, bool) or not isinstance(raw_capacity, int):
                raise ValueError()
            capacity = int(raw_capacity)
            if capacity < 0 or capacity > 5000:
                raise ValueError()
        except (TypeError, ValueError):
            errors.append(f"Salle {key} : capacity doit être un entier de 0 à 5000.")
            capacity = 0
        equipment = _string_list(raw.get("equipment", []), f"Salle {key} : equipment", errors, maximum_items=100, item_maximum=80)
        unavailable = raw.get("unavailable", [])
        if not isinstance(unavailable, list) or len(unavailable) > 500:
            errors.append(f"Salle {key} : unavailable doit être une liste de 500 indisponibilités maximum.")
            unavailable = []
        clean_unavailable = []
        for index, slot in enumerate(unavailable):
            if not isinstance(slot, dict):
                errors.append(f"Salle {key} : unavailable[{index}] doit être un objet.")
                continue
            _check_fields(slot, {"day", "start", "end"}, f"Salle {key} : unavailable[{index}]", errors)
            day = _day(slot.get("day"), f"Salle {key} : jour indisponible", errors)
            start = _time(slot.get("start"), f"Salle {key} : début indisponible", errors)
            end = _time(slot.get("end"), f"Salle {key} : fin indisponible", errors)
            if start is not None and end is not None and start >= end:
                errors.append(f"Salle {key} : une indisponibilité doit finir après son début.")
            clean_unavailable.append({"day": day, "startMinutes": start, "endMinutes": end})
        normalized_name = name.casefold()
        if normalized_name in existing_rooms:
            errors.append(f"La salle {name!r} existe déjà dans Ma Classe.")
        if normalized_name in incoming_room_names:
            errors.append(f"Le nom de salle {name!r} est utilisé plusieurs fois dans le dossier.")
        incoming_room_names.add(normalized_name)
        rooms[key] = {
            "key": key, "name": name, "type": kind, "capacity": capacity,
            "equipment": equipment, "unavailable": clean_unavailable,
        }

    for key, raw in student_records.items():
        first = _text(raw.get("first"), f"students[{key}].first", errors, required=True, maximum=80)
        last = _text(raw.get("last"), f"students[{key}].last", errors, required=True, maximum=80)
        class_key = _key(raw.get("class"), f"students[{key}].class", errors)
        level = _text(raw.get("level", ""), f"students[{key}].level", errors, maximum=40)
        group = _text(raw.get("group", ""), f"students[{key}].group", errors, maximum=80)
        birth = _date(raw.get("birth", ""), f"Élève {key} : birth", errors)
        sex = _text(raw.get("sex", ""), f"Élève {key} : sex", errors, maximum=1).upper()
        if sex not in ("", "F", "M", "X"):
            errors.append(f"Élève {key} : sex doit être F, M, X ou vide.")
            sex = ""
        email = _text(raw.get("email", ""), f"Élève {key} : email", errors, maximum=254)
        phone = _text(raw.get("phone", ""), f"Élève {key} : phone", errors, maximum=40)
        notes = _text(raw.get("notes", ""), f"Élève {key} : notes", errors, maximum=2000)
        if class_key not in classes:
            errors.append(f"Élève {key} : classe {class_key!r} introuvable.")
        else:
            class_record = classes[class_key]
            if level and level not in class_record["levels"]:
                errors.append(f"Élève {key} : niveau {level!r} absent de la classe {class_record['name']!r}.")
            valid_groups = set(class_record["groups"])
            if len(class_record["levels"]) > 1:
                if not level:
                    errors.append(f"Élève {key} : le niveau doit être indiqué pour la classe multi-niveaux {class_record['name']!r}.")
                valid_groups.update(f"{class_record['name']}/{level_name}" for level_name in class_record["levels"])
            if group and group not in valid_groups:
                errors.append(f"Élève {key} : groupe {group!r} non défini pour {class_record['name']!r}.")
        students[key] = {
            "key": key, "first": first, "last": last, "class": class_key,
            "level": level, "group": group, "birth": birth.isoformat() if birth else "",
            "sex": sex, "email": email, "phone": phone, "notes": notes,
        }

    for key, record in classes.items():
        count = sum(1 for student in students.values() if student["class"] == key)
        expected = record["expectedStudentCount"]
        if expected is not None and count != expected and create_student_profiles:
            errors.append(f"Classe {record['name']!r} : {expected} élèves attendus, {count} fiches fournies.")
        if count == 0:
            warnings.append(f"La classe {record['name']!r} ne contient aucun élève.")

    for key, raw in schedule_records.items():
        if raw.get("class") and raw.get("classes"):
            errors.append(f"Créneau {key} : utilise soit class, soit classes, pas les deux.")
        if raw.get("teacher") and raw.get("teachers"):
            errors.append(f"Créneau {key} : utilise soit teacher, soit teachers, pas les deux.")
        class_keys = _key_list(raw.get("classes", [raw.get("class")] if raw.get("class") else []), f"schedule[{key}].classes", errors, maximum_items=100)
        if not class_keys:
            errors.append(f"Créneau {key} : au moins une classe doit être indiquée.")
        for class_key in class_keys:
            if class_key not in classes:
                errors.append(f"Créneau {key} : classe {class_key!r} introuvable.")
        day = _day(raw.get("day"), f"Créneau {key} : day", errors)
        start = _time(raw.get("start"), f"Créneau {key} : start", errors)
        end = _time(raw.get("end"), f"Créneau {key} : end", errors)
        if start is not None and end is not None and start >= end:
            errors.append(f"Créneau {key} : l'heure de fin doit être après l'heure de début.")
        subject = _text(raw.get("subject"), f"Créneau {key} : subject", errors, required=True, maximum=80)
        group = _text(raw.get("group", ""), f"Créneau {key} : group", errors, maximum=80)
        teacher_keys = _key_list(raw.get("teachers", [raw.get("teacher")] if raw.get("teacher") else []), f"Créneau {key} : teachers", errors, maximum_items=20)
        if not teacher_keys:
            errors.append(f"Créneau {key} : au moins un professeur est obligatoire.")
        for teacher_key in teacher_keys:
            if teacher_key not in teachers:
                errors.append(f"Créneau {key} : professeur {teacher_key!r} introuvable.")
            elif subject.casefold() not in {x.casefold() for x in teachers[teacher_key]["subjects"]}:
                errors.append(f"Créneau {key} : {teachers[teacher_key]['first']} {teachers[teacher_key]['last']} n'a pas {subject!r} dans ses matières.")
        room_key = _key(raw.get("room", ""), f"Créneau {key} : room", errors, required=False)
        if room_key and room_key not in rooms:
            errors.append(f"Créneau {key} : salle {room_key!r} introuvable.")
        recurrence = raw.get("recurrence", "weekly")
        if recurrence not in ("weekly", "biweekly", "triweekly", "custom", "once"):
            errors.append(f"Créneau {key} : recurrence non prise en charge.")
            recurrence = "weekly"
        try:
            raw_interval = raw.get("intervalWeeks", 4)
            if recurrence == "custom" and (isinstance(raw_interval, bool) or not isinstance(raw_interval, int)):
                raise ValueError()
            interval = int(raw_interval) if recurrence == "custom" else 1
            if recurrence == "custom" and not 1 <= interval <= 52:
                raise ValueError()
        except (TypeError, ValueError):
            errors.append(f"Créneau {key} : intervalWeeks doit être compris entre 1 et 52.")
            interval = 4
        start_date = _date(raw.get("startDate"), f"Créneau {key} : startDate", errors, required=True)
        end_date = _date(raw.get("endDate", ""), f"Créneau {key} : endDate", errors)
        if start_date and end_date and end_date < start_date:
            errors.append(f"Créneau {key} : endDate précède startDate.")
        exceptions = raw.get("exceptions", [])
        if not isinstance(exceptions, list) or len(exceptions) > 500:
            errors.append(f"Créneau {key} : exceptions doit contenir 500 dates maximum.")
            exceptions = []
        clean_exceptions = []
        for exception in exceptions:
            parsed = _date(exception, f"Créneau {key} : date exceptionnelle", errors, required=True)
            if parsed:
                clean_exceptions.append(parsed.isoformat())
        equipment = _string_list(raw.get("equipment", []), f"Créneau {key} : equipment", errors, maximum_items=30, item_maximum=80)
        if day is not None and start is not None and end is not None and start_date:
            record = {
                "key": key, "classes": class_keys, "day": day,
                "start": raw.get("start"), "end": raw.get("end"),
                "startMinutes": start, "endMinutes": end, "subject": subject,
                "group": group, "teachers": teacher_keys, "room": room_key,
                "recurrence": recurrence, "intervalWeeks": interval,
                "startDate": start_date, "endDate": end_date,
                "exceptions": clean_exceptions, "equipment": equipment,
            }
            schedule[key] = record

    # Préindexe les effectifs pour éviter de reparcourir tous les élèves
    # pour chaque créneau et chaque salle.
    student_count_by_class = defaultdict(int)
    student_count_by_class_group = defaultdict(int)
    for student in students.values():
        class_key = student["class"]
        student_count_by_class[class_key] += 1
        effective_group = student["group"]
        classroom = classes.get(class_key)
        if (
            not effective_group
            and classroom
            and student["level"]
            and len(classroom["levels"]) > 1
        ):
            # build_data() assigns this generated cohort when importing a
            # multi-level student whose group was omitted from the JSON.
            effective_group = f'{classroom["name"]}/{student["level"]}'
        if effective_group:
            student_count_by_class_group[(class_key, effective_group)] += 1

    # Les affectations de classe sont la réunion des listes classe/professeur
    # et des professeurs réellement présents dans les cours.
    for class_key, class_record in classes.items():
        assigned = set(class_record["teachers"])
        if class_record["principalTeacher"]:
            assigned.add(class_record["principalTeacher"])
        for teacher_key, teacher_record in teachers.items():
            if class_key in teacher_record["classes"]:
                assigned.add(teacher_key)
        class_record["teachers"] = sorted(assigned)
        if class_record["principalTeacher"] and class_record["principalTeacher"] not in assigned:
            errors.append(f"Le professeur principal de {class_record['name']!r} doit être affecté à cette classe.")

    # Une affectation à une matière doit aussi être cohérente avec l'affectation de classe.
    for lesson in schedule.values():
        for class_key in lesson["classes"]:
            if class_key in classes:
                for teacher_key in lesson["teachers"]:
                    if teacher_key in teachers and teacher_key not in classes[class_key]["teachers"]:
                        errors.append(f"Créneau {lesson['key']} : {teacher_key!r} n'est pas affecté à {classes[class_key]['name']!r}.")
            if lesson["group"] and class_key in classes:
                class_record = classes[class_key]
                groups = set(class_record["groups"])
                if len(class_record["levels"]) > 1:
                    groups.update(f"{class_record['name']}/{level}" for level in class_record["levels"])
                if lesson["group"] not in groups:
                    errors.append(f"Créneau {lesson['key']} : groupe {lesson['group']!r} non défini dans {class_record['name']!r}.")
        if lesson["room"] and lesson["room"] in rooms:
            room = rooms[lesson["room"]]
            # A shared lesson can target several classes. Capacity applies to
            # the combined cohort, not independently to each generated row.
            if lesson["group"]:
                student_count = sum(
                    student_count_by_class_group[(class_key, lesson["group"])]
                    for class_key in lesson["classes"]
                )
            else:
                student_count = sum(
                    student_count_by_class[class_key]
                    for class_key in lesson["classes"]
                )
            if student_count == 0 and not bundle.get("createStudentProfiles", True):
                # With no imported student records, use the expected class sizes.
                student_count = sum(
                    int(classes[class_key].get("expectedStudentCount") or 0)
                    for class_key in lesson["classes"] if class_key in classes
                )
            if room["capacity"] and student_count > room["capacity"]:
                errors.append(f"Créneau {lesson['key']} : la salle {room['name']!r} ({room['capacity']} places) est trop petite pour {student_count} élèves.")
            missing_equipment = [
                need for need in lesson["equipment"]
                if not any(need.casefold() in offered.casefold() for offered in room["equipment"])
            ]
            if missing_equipment:
                errors.append(f"Créneau {lesson['key']} : la salle {room['name']!r} ne possède pas : {', '.join(missing_equipment)}.")
            for unavailable in room["unavailable"]:
                if unavailable["day"] == lesson["day"] and unavailable["startMinutes"] is not None and unavailable["endMinutes"] is not None:
                    if lesson["startMinutes"] < unavailable["endMinutes"] and unavailable["startMinutes"] < lesson["endMinutes"]:
                        errors.append(f"Créneau {lesson['key']} : la salle {room['name']!r} est indisponible sur ce créneau.")
        for teacher_key in lesson["teachers"]:
            teacher = teachers.get(teacher_key)
            if teacher:
                for unavailable in teacher["unavailable"]:
                    if unavailable["day"] == lesson["day"] and unavailable["startMinutes"] is not None and unavailable["endMinutes"] is not None:
                        if lesson["startMinutes"] < unavailable["endMinutes"] and unavailable["startMinutes"] < lesson["endMinutes"]:
                            errors.append(f"Créneau {lesson['key']} : {teacher['first']} {teacher['last']} est indisponible à cet horaire.")

    # Indexe les créneaux par classe et jour pour les calculs suivants.
    # Les mêmes index servent aux besoins horaires et aux indicateurs de trous.
    lessons = list(schedule.values())
    lessons_by_class = defaultdict(list)
    class_day_lessons = defaultdict(list)
    teacher_day_lessons = defaultdict(list)
    for lesson in lessons:
        for class_key in lesson["classes"]:
            lessons_by_class[class_key].append(lesson)
            if lesson["recurrence"] == "weekly":
                class_day_lessons[(class_key, lesson["day"])].append(lesson)
        if lesson["recurrence"] == "weekly":
            for teacher_key in lesson["teachers"]:
                teacher_day_lessons[(teacher_key, lesson["day"])].append(lesson)

    # Détecte les conflits uniquement entre créneaux partageant une ressource.
    for left_index, right_index in _iter_resource_overlap_pairs(lessons):
        left, right = lessons[left_index], lessons[right_index]
        if not _recurrences_overlap(left, right):
            continue
        shared_classes = set(left["classes"]) & set(right["classes"])
        same_class_conflict = any(
            _groups_overlap(left["group"], right["group"]) for _ in shared_classes
        )
        same_teacher_conflict = bool(set(left["teachers"]) & set(right["teachers"]))
        same_room_conflict = bool(left["room"] and right["room"] and left["room"] == right["room"])
        if same_class_conflict or same_teacher_conflict or same_room_conflict:
            reasons = []
            if same_class_conflict:
                reasons.append("classe/groupe")
            if same_teacher_conflict:
                reasons.append("professeur")
            if same_room_conflict:
                reasons.append("salle")
            errors.append(
                f"Conflit entre les créneaux {left['key']} et {right['key']} ({', '.join(reasons)})."
            )
            # La réponse publique est de toute façon limitée à 200 erreurs.
            # Arrêter tôt évite d'énumérer des millions de paires toutes invalides.
            if len(errors) >= 200:
                break

    for class_key, class_record in classes.items():
        all_groups = set(class_record["groups"])
        if len(class_record["levels"]) > 1:
            all_groups.update(f"{class_record['name']}/{level}" for level in class_record["levels"])
        all_groups.update(
            student["group"] for student in students.values()
            if student["class"] == class_key and student["group"]
        )
        for requirement in class_record["subjectRequirements"]:
            requested_group = requirement["group"]
            if requested_group and requested_group not in all_groups:
                errors.append(
                    f"Classe {class_record['name']!r} : le groupe {requested_group!r} "
                    "de la répartition horaire n'existe pas."
                )
                continue
            cohorts = [requested_group] if requested_group else (sorted(all_groups) if all_groups else [""])
            for cohort in cohorts:
                supplied = 0.0
                for lesson in lessons_by_class.get(class_key, ()):
                    if lesson["subject"].casefold() != requirement["subject"].casefold():
                        continue
                    if lesson["group"] and lesson["group"] != cohort:
                        continue
                    if lesson["recurrence"] == "once":
                        continue
                    supplied += (
                        (lesson["endMinutes"] - lesson["startMinutes"])
                        / 60.0
                        / _period_weeks(lesson)
                    )
                if abs(supplied - requirement["hoursPerWeek"]) > 0.01:
                    cohort_label = f" ({cohort})" if cohort else ""
                    errors.append(
                        f"Classe {class_record['name']!r}{cohort_label} : {requirement['subject']} prévoit "
                        f"{requirement['hoursPerWeek']:g} h/semaine mais le planning en fournit {supplied:g}."
                    )

    if not classes:
        errors.append("Le dossier doit contenir au moins une classe.")
    if not students:
        warnings.append("Aucune fiche élève ne sera créée.")
    if not teachers:
        warnings.append("Aucun compte professeur ne sera créé.")
    if not schedule:
        warnings.append("Aucun créneau d'emploi du temps ne sera créé.")

    # Contrôle de densité calculé par cohorte (classe/groupe), afin que deux
    # cours parallèles de groupes distincts ne créent pas de faux trous.
    gap_days = 0
    gap_minutes = 0
    for class_key, class_record in classes.items():
        cohorts = set(class_record["groups"])
        if len(class_record["levels"]) > 1:
            cohorts.update(f"{class_record['name']}/{level}" for level in class_record["levels"])
        cohorts.update(student["group"] for student in students.values() if student["class"] == class_key and student["group"])
        if not cohorts:
            cohorts.add("")
        for day in range(5):
            for cohort in cohorts:
                daily = [
                    lesson for lesson in class_day_lessons.get((class_key, day), ())
                    if not lesson["group"] or lesson["group"] == cohort
                ]
                if not daily:
                    continue
                ordered = sorted(daily, key=lambda x: x["startMinutes"])
                gaps = sum(max(0, ordered[i + 1]["startMinutes"] - ordered[i]["endMinutes"]) for i in range(len(ordered) - 1))
                if gaps:
                    gap_days += 1
                    gap_minutes += gaps
                    if gaps > 90:
                        warnings.append(f"L'emploi du temps de {class_record['name']} ({cohort or 'classe entière'}) contient plus de 1 h 30 de trous sur une journée.")

    teacher_gap_days = 0
    teacher_gap_minutes = 0
    for teacher_key, teacher_record in teachers.items():
        for day in range(5):
            daily = teacher_day_lessons.get((teacher_key, day), [])
            if not daily:
                continue
            ordered = sorted(daily, key=lambda x: x["startMinutes"])
            gaps = sum(max(0, ordered[i + 1]["startMinutes"] - ordered[i]["endMinutes"]) for i in range(len(ordered) - 1))
            if gaps:
                teacher_gap_days += 1
                teacher_gap_minutes += gaps
                if gaps > 120:
                    warnings.append(f"L'emploi du temps de {teacher_record['first']} {teacher_record['last']} contient plus de 2 h de trous sur une journée.")
    quality = {"classDaysWithGaps": gap_days, "weeklyGapHours": round(gap_minutes / 60, 2), "teacherDaysWithGaps": teacher_gap_days, "teacherWeeklyGapHours": round(teacher_gap_minutes / 60, 2)}
    if errors:
        # Keep diagnostics bounded for the UI and avoid an enormous server response.
        errors = list(dict.fromkeys(errors))[:200]
    warnings = list(dict.fromkeys(warnings))[:100]
    return {
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "establishment": establishment_name,
            "classes": len(classes), "students": len(students) if create_student_profiles else 0,
            "teachers": len(teachers), "teacherAccounts": len(teachers) if create_teacher_accounts else 0, "rooms": len(rooms),
            "scheduleSlots": len(schedule),
        },
        "quality": quality,
        "_normalized": {
            "establishment": {"name": establishment_name},
            "classes": classes, "students": students, "teachers": teachers,
            "createTeacherAccounts": create_teacher_accounts,
            "createStudentProfiles": create_student_profiles,
            "rooms": rooms, "schedule": schedule,
        },
    }


def build_data(bundle, existing_data, *, password_hasher, token_factory):
    """Return a merged DB, one-time teacher credentials, and a public summary.

    Only new records are created: existing classes/rooms are never overwritten.
    All identifiers and passwords are generated locally by the server.
    """
    if existing_data is not None and not isinstance(existing_data, dict):
        raise ValueError(
            "Données existantes incompatibles : la racine de la base n'est pas un objet. "
            "Aucune donnée n'a été remplacée."
        )
    source_data = existing_data if isinstance(existing_data, dict) else {}
    collection_names = (
        "classes", "students", "users", "teachers", "schedule", "teacherAssignments",
        "lessons", "evaluations", "attendance", "bulletins", "submissions",
    )
    # Do not silently replace malformed existing records with empty lists.
    # An import is additive: if a persisted collection has an unexpected
    # shape, fail before validation/building rather than discard user data.
    for name in collection_names:
        if name in source_data and not isinstance(source_data[name], list):
            raise ValueError(
                f"Données existantes incompatibles : le champ {name!r} n'est pas une liste. "
                "Aucune donnée n'a été remplacée."
            )
    if "settings" in source_data and not isinstance(source_data["settings"], dict):
        raise ValueError(
            "Données existantes incompatibles : les paramètres ne sont pas un objet. "
            "Aucune donnée n'a été remplacée."
        )
    existing_settings = source_data.get("settings", {})
    if (
        isinstance(existing_settings, dict)
        and "rooms" in existing_settings
        and not isinstance(existing_settings["rooms"], list)
    ):
        raise ValueError(
            "Données existantes incompatibles : la liste des salles est invalide. "
            "Aucune donnée n'a été remplacée."
        )

    validation = validate_bundle(bundle, source_data)
    if validation["errors"]:
        raise ValueError(validation["errors"][0])
    normalized = validation["_normalized"]
    data = copy.deepcopy(source_data)
    for name in collection_names:
        data.setdefault(name, [])
    data.setdefault("settings", {})
    data["settings"].setdefault("rooms", [])

    teacher_ids = {}
    teacher_credentials = []
    used_usernames = {str(user.get("username", "")).casefold() for user in data["users"] if isinstance(user, dict)}
    for key, teacher in normalized["teachers"].items():
        user_id = token_factory(18)
        teacher_profile = {
            "id": user_id, "teacherId": user_id, "role": "teacher",
            "first": teacher["first"], "last": teacher["last"],
            "name": f"{teacher['first']} {teacher['last']}".strip(),
            "email": teacher["email"], "phone": teacher["phone"],
            "subjects": teacher["subjects"], "profileNotes": teacher["profileNotes"],
            "active": True, "scheduleUnavailable": teacher["unavailable"],
        }
        data["teachers"].append(teacher_profile)
        teacher_ids[key] = user_id
        if not normalized.get("createTeacherAccounts", True):
            continue
        username = teacher["username"] or _username_base(teacher)
        base = username
        suffix = 2
        while username.casefold() in used_usernames:
            if teacher["username"]:
                raise ValueError(f"Identifiant professeur {username!r} déjà utilisé.")
            suffix_text = f".{suffix}"
            username = base[:40 - len(suffix_text)] + suffix_text
            suffix += 1
        used_usernames.add(username.casefold())
        temporary_password = token_factory(10)
        account = {
            **teacher_profile,
            "username": username,
            "mustChangePassword": True,
            "passwordHash": password_hasher(temporary_password),
        }
        data["users"].append(account)
        teacher_credentials.append({
            "first": teacher["first"], "last": teacher["last"],
            "username": username, "temporaryPassword": temporary_password,
        })

    class_ids = {}
    for key, classroom in normalized["classes"].items():
        class_id = token_factory(18)
        class_ids[key] = class_id
        levels = classroom["levels"]
        auto_groups = [f"{classroom['name']}/{level}" for level in levels] if len(levels) > 1 else []
        groups = list(dict.fromkeys(auto_groups + classroom["groups"]))
        assigned = set(teacher_ids[t] for t in classroom["teachers"] if t in teacher_ids)
        principal_id = teacher_ids.get(classroom["principalTeacher"], "")
        if principal_id:
            assigned.add(principal_id)
        data["classes"].append({
            "id": class_id, "name": classroom["name"],
            "level": "/".join(levels), "levels": levels,
            "doubleLevel": len(levels) > 1, "group": "",
            "groups": groups, "attendanceMode": classroom["attendanceMode"],
            "periodMode": classroom["periodMode"],
            "subjectRequirements": classroom["subjectRequirements"],
            "teacherIds": sorted(assigned), "principalTeacherId": principal_id,
        })

    for key, student in normalized["students"].items():
        class_id = class_ids[student["class"]]
        classroom = normalized["classes"][student["class"]]
        group = student["group"]
        if not group and student["level"] and len(classroom["levels"]) > 1:
            group = f"{classroom['name']}/{student['level']}"
        student_level = student["level"] or (classroom["levels"][0] if len(classroom["levels"]) == 1 else "")
        data["students"].append({
            "id": token_factory(18), "first": student["first"], "last": student["last"],
            "birth": student["birth"], "sex": student["sex"], "classId": class_id,
            "level": student_level, "group": group, "email": student["email"], "phone": student["phone"],
            "notes": student["notes"],
        })

    room_ids = {}
    for key, room in normalized["rooms"].items():
        room_id = token_factory(18)
        room_ids[key] = room_id
        data["settings"]["rooms"].append({
            "id": room_id, "name": room["name"], "type": room["type"],
            "capacity": room["capacity"], "equipment": room["equipment"],
            "unavailable": room["unavailable"],
        })

    for key, lesson in normalized["schedule"].items():
        shared_id = token_factory(18)
        teacher_list = [teacher_ids[t] for t in lesson["teachers"] if t in teacher_ids]
        room = normalized["rooms"].get(lesson["room"]) if lesson["room"] else None
        for class_key in lesson["classes"]:
            class_id = class_ids[class_key]
            data["schedule"].append({
                "id": token_factory(18), "sharedSlotId": shared_id,
                "classId": class_id, "day": lesson["day"],
                "time": lesson["start"], "endTime": lesson["end"],
                "subject": lesson["subject"], "group": lesson["group"],
                "teacherId": teacher_list[0] if teacher_list else "",
                "teacherIds": teacher_list,
                "room": room["name"] if room else "",
                "roomId": room_ids.get(lesson["room"], ""),
                "recurrence": lesson["recurrence"],
                "intervalWeeks": lesson["intervalWeeks"],
                "startDate": lesson["startDate"].isoformat(),
                "endDate": lesson["endDate"].isoformat() if lesson["endDate"] else "",
                "exceptions": lesson["exceptions"], "pattern": "none",
                "courseId": "|".join([class_id, lesson["subject"], teacher_list[0] if teacher_list else "", lesson["group"]]),
                "requiredEquipment": lesson["equipment"],
            })

    audit = data.get("auditLog")
    if not isinstance(audit, list):
        audit = []
    audit.insert(0, {
        "id": token_factory(12), "at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "actor": "Direction", "action": "Import d'une configuration d'établissement",
        "detail": normalized["establishment"]["name"] or f"{len(class_ids)} classe(s)",
    })
    data["auditLog"] = audit[:300]
    return data, teacher_credentials, validation["summary"]


def public_validation(validation):
    """Strip internal normalized records before returning the preview to the browser."""
    return {
        "valid": not bool(validation.get("errors")),
        "errors": validation.get("errors", []),
        "warnings": validation.get("warnings", []),
        "summary": validation.get("summary", {}),
        "quality": validation.get("quality", {}),
    }
