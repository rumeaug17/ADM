import bcrypt
import mysql.connector
import sys

def main():
    if len(sys.argv) != 3:
        print("Usage : python create_user.py <username> <password>")
        sys.exit(1)

    username = sys.argv[1]
    plain_password = sys.argv[2]

    # Configuration de connexion à MySQL
    db_config = {
        "host": "localhost",
        "user": "auth_user",        # à adapter
        "password": "auth_pass",    # à adapter
        "database": "users_db"      # à adapter
    }

    # Hash du mot de passe avec bcrypt
    hashed_password = bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()

    # Connexion à la base de données et insertion
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, hashed_password)
        )
        conn.commit()
        print(f"✅ Utilisateur '{username}' créé avec succès.")
    except mysql.connector.Error as err:
        print(f"❌ Erreur MySQL : {err}")
    except Exception as e:
        print(f"❌ Erreur : {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
