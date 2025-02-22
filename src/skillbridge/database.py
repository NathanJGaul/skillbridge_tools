"""Database operations for Skillbridge opportunities."""

import json
from datetime import datetime
from typing import List, Dict, Any
import psycopg2

from .schema import SkillbridgeSchema

def save_to_json(data: List[dict], filename: str = None) -> None:
    """Saves data to a JSON file."""
    if filename is None:
        filename = f"opportunities_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Data saved to {filename}")

def store_data_in_db(connection_string: str, data: List[dict]) -> None:
    """Stores or updates scraped data in the PostgreSQL database."""
    try:
        with psycopg2.connect(connection_string) as conn:
            with conn.cursor() as cur:
                # Get existing records
                columns = SkillbridgeSchema.get_db_columns()
                columns_str = ", ".join(columns)
                cur.execute(f"SELECT {columns_str} FROM skillbridge_opportunities")
                existing_records = {}
                for record in cur.fetchall():
                    record_dict = dict(zip(columns, record))
                    identifier = SkillbridgeSchema.generate_identifier(record_dict)
                    existing_records[identifier] = record_dict

                # Process each new record
                for item in data:
                    identifier = SkillbridgeSchema.generate_identifier(item)
                    values = SkillbridgeSchema.get_db_values(item)
                    
                    if identifier in existing_records:
                        if SkillbridgeSchema.has_changes(item, existing_records[identifier]):
                            # Update existing record
                            set_clause = ", ".join([f"{col} = %s" for col in columns])
                            update_query = f"""
                                UPDATE skillbridge_opportunities
                                SET {set_clause}
                                WHERE partner_program_agency = %s
                                AND city = %s
                                AND state = %s;
                            """
                            # Add identifier fields to values for WHERE clause
                            update_values = values + (
                                item.get('partner_program_agency'),
                                item.get('city'),
                                item.get('state')
                            )
                            cur.execute(update_query, update_values)
                    else:
                        # Insert new record
                        placeholders = ", ".join(["%s"] * len(columns))
                        insert_query = f"""
                            INSERT INTO skillbridge_opportunities (
                                {columns_str}
                            ) VALUES ({placeholders});
                        """
                        cur.execute(insert_query, values)

                conn.commit()
                print("Data successfully synchronized in the database.")

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
        raise
