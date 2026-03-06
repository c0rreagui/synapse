import psycopg2

def fix_schema():
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="synapse_db",
            user="synapse",
            password="synapse_password"
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        columns = [
            ("proxy_server", "VARCHAR"),
            ("proxy_username", "VARCHAR"),
            ("proxy_password", "VARCHAR"),
            ("fingerprint_ua", "VARCHAR"),
            ("fingerprint_viewport_w", "INTEGER"),
            ("fingerprint_viewport_h", "INTEGER"),
            ("fingerprint_locale", "VARCHAR"),
            ("fingerprint_timezone", "VARCHAR"),
            ("geolocation_latitude", "VARCHAR"),
            ("geolocation_longitude", "VARCHAR")
        ]
        
        for col_name, col_type in columns:
            try:
                cur.execute(f"ALTER TABLE profiles ADD COLUMN {col_name} {col_type};")
                print(f"Added column: {col_name}")
            except psycopg2.errors.DuplicateColumn:
                print(f"Column already exists: {col_name}")
                # needs to be ignored, autocommit=True handles this easily since it rolls back just the statement
            except Exception as e:
                print(f"Error on {col_name}: {str(e)}")
                
        # also apply proxy nickname to proxies table just in case It's missing
        try:
            cur.execute("ALTER TABLE proxies ADD COLUMN nickname VARCHAR;")
            print("Added nickname to proxies table")
        except:
             pass

    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    fix_schema()
