import io
import os
import zipfile


def get_backup_files(config_dir, data_dir, base_dir, add_log_entry):
    """Return all user/config files that should be included in backup/restore."""
    allowed_extra_files = {
        "internal_mosquitto.conf",
        "internal_mosquitto.passwd",
    }

    result = {}

    try:
        search_dirs = []
        for folder in (config_dir, data_dir, base_dir):
            if folder and os.path.isdir(folder) and folder not in search_dirs:
                search_dirs.append(folder)

        for folder in search_dirs:
            for filename in os.listdir(folder):
                path = os.path.join(folder, filename)

                if not os.path.isfile(path):
                    continue

                clean_name = os.path.basename(filename)

                if clean_name.lower().endswith(".json"):
                    result[clean_name] = path
                elif clean_name in allowed_extra_files:
                    result[clean_name] = path

    except Exception as e:
        add_log_entry(f"Backup Dateisuche Fehler: {e}")

    return dict(sorted(result.items(), key=lambda item: item[0].lower()))


def backup_config(files_to_backup, add_log_entry, send_file, redirect):
    memory_file = io.BytesIO()

    try:
        with zipfile.ZipFile(memory_file, "w", zipfile.ZIP_DEFLATED) as zf:
            for backup_name, file_path in files_to_backup.items():
                if os.path.exists(file_path):
                    zf.write(file_path, backup_name)
                    add_log_entry(f"Backup: {backup_name} gesichert")
                else:
                    add_log_entry(f"Backup: {backup_name} fehlt, übersprungen")

        memory_file.seek(0)
        add_log_entry("Backup vollständig erstellt")

        return send_file(
            memory_file,
            as_attachment=True,
            download_name="mqtt2lox_backup.zip",
            mimetype="application/zip"
        )

    except Exception as e:
        add_log_entry(f"Backup Fehler: {e}")
        return redirect("/")


def restore_config(file_storage, allowed_files, add_log_entry, redirect):
    try:
        memory_file = io.BytesIO(file_storage.read())

        with zipfile.ZipFile(memory_file, "r") as zf:
            for filename in zf.namelist():
                clean_name = os.path.basename(filename)

                if clean_name not in allowed_files:
                    add_log_entry(f"Restore: {filename} ignoriert")
                    continue

                target_path = allowed_files[clean_name]

                with open(target_path, "wb") as f:
                    f.write(zf.read(filename))

                add_log_entry(f"Restore: {clean_name} wiederhergestellt")

        add_log_entry("Backup vollständig wiederhergestellt")

    except Exception as e:
        add_log_entry(f"Restore Fehler: {e}")

    return redirect("/")
