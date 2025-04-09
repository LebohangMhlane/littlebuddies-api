import os

def delete_migration_files():
    for root, dirs, files in os.walk(os.getcwd()):
        if "migrations" in root.split(
            os.sep
        ):  # Ensure we're inside a migrations folder
            for file in files:
                if (
                    file.endswith(".py")
                    and file != "__init__.py"
                    or file.endswith(".pyc")
                ):
                    file_path = os.path.join(root, file)
                    os.remove(file_path)
                    print(f"Deleted: {file_path}")


if __name__ == "__main__":
    delete_migration_files()
    print("All migration files deleted successfully.")
