# app/members/routes.py
from flask import request, jsonify, current_app, Blueprint
import mysql.connector
import hashlib
from datetime import *

# Import helpers and decorators
from ..utils.database import get_cims_db_connection
from ..auth.decorators import token_required

# Create the Blueprint instance
members_bp = Blueprint('members', __name__) # 'members' is the blueprint name

# --- Task 1 Endpoint: Add Member (Admin Only) ---
@members_bp.route('/admin/add_member', methods=['POST'])
@token_required
def add_member_task1(current_user_id, current_user_role):
    """Task 1: Adds member/login. Requires LOCAL Admin auth."""
    current_app.logger.info(f"Request: /admin/add_member by user ID: {current_user_id}, Role: {current_user_role}")

    if current_user_role != 'admin':
        current_app.logger.warning(f"Access denied: User {current_user_id} (Role: {current_user_role}) is not admin.")
        return jsonify({"error": "Admin privileges required"}), 403

    current_app.logger.info(f"Admin user {current_user_id} authorized. Adding member.")

    try:
        data = request.get_json()
        if not data or 'UserName' not in data:
            current_app.logger.warning("Missing 'UserName' in add_member request")
            return jsonify({"error": "Missing 'Username' in request JSON body"}), 400
        new_name = data['UserName']
        if 'emailID' in data:
            new_email = data['emailID']
        if 'DoB' in data:
            new_DoB = data['DoB']
        if 'Role' in data:
            new_role = data['Role']
        else :
            new_role = 'user'
    except Exception as e:
        current_app.logger.error(f"Error parsing add_member request JSON: {e}")
        return jsonify({"error": "Invalid JSON data in request body"}), 400

    conn = None
    cursor = None
    new_member_id = None
    try:
        conn = get_cims_db_connection()
        if not conn: return jsonify({"error": "Database connection failed"}), 500
        cursor = conn.cursor()

        # Insert into members (Use correct column names: UserName, emailID)
        sql_insert_member = "INSERT INTO members (UserName, emailID, DoB) VALUES (%s, %s, %s)"
        cursor.execute(sql_insert_member, (new_name, new_email, new_DoB))
        current_app.logger.info(f"Executed INSERT members for '{new_name}'.")

        new_member_id = cursor.lastrowid
        if not new_member_id:
            raise mysql.connector.Error("Failed to retrieve last inserted ID from members.")
        current_app.logger.info(f"New member ID: {new_member_id}")

        # Hash default password (using MD5 for consistency as decided earlier)
        default_password = current_app.config['DEFAULT_PASSWORD']
        hashed_default_password = hashlib.md5(default_password.encode()).hexdigest()

        # Insert into Login (Use correct table and column names: Login, MemberID, Password, Role)
        sql_insert_login = "INSERT INTO Login (MemberID, Password, Role) VALUES (%s, %s, %s)"
        cursor.execute(sql_insert_login, (new_member_id, hashed_default_password, new_role))        
        current_app.logger.info(f"Executed INSERT Login for MemberID {new_member_id}.")

        conn.commit()
        current_app.logger.info(f"DB transaction committed for new member {new_member_id}.")

        return jsonify({
            "message": "Task 1 Success: Member created and login entry added (using local auth).",
            "ID": new_member_id,
        }), 201

    except mysql.connector.Error as db_err:
        current_app.logger.error(f"Database Error during Task 1: {db_err}")
        if conn: conn.rollback(); current_app.logger.info("DB transaction rolled back.")
        # Check specifically for duplicate key error
        if db_err.errno == 1062: # MySQL error code for duplicate entry
             return jsonify({"error": "Duplicate entry detected. MemberID might already exist in Login table.", "details": str(db_err)}), 409 # 409 Conflict
        return jsonify({"error": "Database error occurred", "details": str(db_err)}), 500
    except Exception as e:
        current_app.logger.error(f"Unexpected error during Task 1: {e}", exc_info=True)
        if conn: conn.rollback(); current_app.logger.info("DB transaction rolled back.")
        return jsonify({"error": "An internal server error occurred", "details": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


# --- Task 2 Demo: View Own Profile ---
@members_bp.route('/profile/me', methods=['GET'])
@token_required
def get_my_profile(current_user_id, current_user_role):
    """Allows any authenticated user to view their own profile."""
    current_app.logger.info(f"Request: /profile/me by user ID: {current_user_id}, Role: {current_user_role}")
    conn = None
    cursor = None
    try:
        conn = get_cims_db_connection()
        if not conn: return jsonify({"error": "Database connection failed"}), 500
        cursor = conn.cursor(dictionary=True)

        # Use correct column names (ID, UserName, emailID, DoB)
        sql_select_me = "SELECT ID, UserName, emailID, DoB FROM members WHERE ID = %s"
        cursor.execute(sql_select_me, (current_user_id,))
        profile_data = cursor.fetchone()

        if not profile_data:
            current_app.logger.warning(f"Profile data not found for user ID: {current_user_id}")
            return jsonify({"error": "Profile data not found"}), 404

        current_app.logger.info(f"Retrieved profile for user ID: {current_user_id}")
        return jsonify(profile_data), 200

    except mysql.connector.Error as db_err:
         current_app.logger.error(f"Database Error in /profile/me: {db_err}")
         return jsonify({"error": "Database error", "details": str(db_err)}), 500
    except Exception as e:
        current_app.logger.error(f"Unexpected error in /profile/me: {e}", exc_info=True)
        return jsonify({"error": "Internal server error", "details": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


# --- Task 2 Demo: View Any Profile (Admin Only) ---
@members_bp.route('/admin/profile/<int:target_member_id>', methods=['GET'])
@token_required
def get_any_profile(current_user_id, current_user_role, target_member_id):
    """Allows ONLY admins to view any member profile by ID."""
    current_app.logger.info(f"Request: /admin/profile/{target_member_id} by user ID: {current_user_id}, Role: {current_user_role}")

    if current_user_role != 'admin':
        current_app.logger.warning(f"Access denied: User {current_user_id} (Role: {current_user_role}) is not admin for /admin/profile.")
        return jsonify({"error": "Admin privileges required"}), 403

    current_app.logger.info(f"Admin user {current_user_id} authorized. Fetching profile for target: {target_member_id}")
    conn = None
    cursor = None
    try:
        conn = get_cims_db_connection()
        if not conn: return jsonify({"error": "Database connection failed"}), 500
        cursor = conn.cursor(dictionary=True)

        # Use correct column names
        sql_select_target = "SELECT ID, UserName, emailID, DoB FROM members WHERE ID = %s"
        cursor.execute(sql_select_target, (target_member_id,))
        profile_data = cursor.fetchone()

        if not profile_data:
            current_app.logger.warning(f"Admin {current_user_id} requested non-existent profile ID: {target_member_id}")
            return jsonify({"error": f"Member with ID {target_member_id} not found"}), 404

        current_app.logger.info(f"Admin {current_user_id} retrieved profile for ID: {target_member_id}")
        return jsonify(profile_data), 200

    except mysql.connector.Error as db_err:
        current_app.logger.error(f"Database Error in /admin/profile: {db_err}")
        return jsonify({"error": "Database error", "details": str(db_err)}), 500
    except Exception as e:
        current_app.logger.error(f"Unexpected error in /admin/profile: {e}", exc_info=True)
        return jsonify({"error": "Internal server error", "details": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()
        
# --- ***** Task 3 Endpoint: Delete Member (Admin Only) ***** ---
@members_bp.route('/admin/delete_member/<int:member_id_to_delete>', methods=['DELETE'])
@token_required
def delete_member_task3(current_user_id, current_user_role, member_id_to_delete):
    """
    Task 3: Deletes a member conditionally based on group mappings.
    Requires LOCAL Admin authentication.
    """
    current_app.logger.info(f"Request: /admin/delete_member/{member_id_to_delete} by Admin ID: {current_user_id}")

    # 1. RBAC Check (Admin Only)
    if current_user_role != 'admin':
        current_app.logger.warning(f"Access denied: User {current_user_id} (Role: {current_user_role}) cannot delete members.")
        return jsonify({"error": "Admin privileges required to delete members"}), 403

    # 2. Check if Member Exists (Optional but good practice)
    conn = None
    cursor = None
    try:
        conn = get_cims_db_connection()
        if not conn: return jsonify({"error": "Database connection failed"}), 500
        cursor = conn.cursor(dictionary=True) # Use dictionary cursor for easier access

        # Check if member exists in members table first
        cursor.execute("SELECT ID FROM members WHERE ID = %s", (member_id_to_delete,))
        member_exists = cursor.fetchone()
        if not member_exists:
            current_app.logger.warning(f"Admin {current_user_id} tried to delete non-existent MemberID: {member_id_to_delete}")
            return jsonify({"error": f"Member with ID {member_id_to_delete} not found in members table."}), 404

        # 3. Check Group Mappings
        # Ensure correct column names for MemberGroupMapping (assuming MemberID)
        sql_check_mapping = "SELECT COUNT(*) as mapping_count FROM MemberGroupMapping WHERE MemberID = %s"
        cursor.execute(sql_check_mapping, (member_id_to_delete,))
        result = cursor.fetchone()
        mapping_count = result['mapping_count'] if result else 0
        current_app.logger.info(f"MemberID {member_id_to_delete} found in {mapping_count} group mappings.")

        # Use a transaction for the deletion steps
        # conn.start_transaction()
        deleted_from_login = 0
        deleted_from_members = 0
        deleted_from_mapping = 0
        message = ""

        # 4. Conditional Deletion Logic
        if mapping_count == 0:
            # Case 1: Member is in NO groups - Delete fully
            current_app.logger.info(f"MemberID {member_id_to_delete} has no group mappings. Proceeding with full deletion.")

            # Delete from Login table (Use correct table/column names)
            sql_delete_login = "DELETE FROM Login WHERE MemberID = %s"
            cursor.execute(sql_delete_login, (member_id_to_delete,))
            deleted_from_login = cursor.rowcount
            current_app.logger.info(f"Deleted {deleted_from_login} row(s) from Login for MemberID {member_id_to_delete}.")

            # Delete from members table (Use correct table/column names)
            sql_delete_members = "DELETE FROM members WHERE ID = %s"
            cursor.execute(sql_delete_members, (member_id_to_delete,))
            deleted_from_members = cursor.rowcount
            current_app.logger.info(f"Deleted {deleted_from_members} row(s) from members for ID {member_id_to_delete}.")

            if deleted_from_members > 0: # Check if deletion from members actually happened
                 message = f"Member {member_id_to_delete} deleted successfully from members and Login tables."
            else:
                 # Should not happen if member_exists check passed, but good to handle
                 message = f"Member {member_id_to_delete} not found in members table during deletion (unexpected)."
                 # Might indicate a race condition or issue, consider raising error or rolling back implicitly


        else:
            # Case 2: Member IS in other groups - Delete only specific mapping
            our_group_id = current_app.config.get('GROUP_ID', 'cs432g2') # Get from config
            current_app.logger.info(f"MemberID {member_id_to_delete} has group mappings. Deleting mapping for group '{our_group_id}'.")

            # Delete specific mapping (Use correct table/column names: MemberGroupMapping, MemberID, GroupID)
            sql_delete_mapping = "DELETE FROM MemberGroupMapping WHERE MemberID = %s AND GroupID = %s"
            cursor.execute(sql_delete_mapping, (member_id_to_delete, our_group_id))
            deleted_from_mapping = cursor.rowcount
            current_app.logger.info(f"Deleted {deleted_from_mapping} mapping(s) for MemberID {member_id_to_delete} and GroupID {our_group_id}.")

            if deleted_from_mapping > 0:
                 message = f"Removed association for Member {member_id_to_delete} with Group {our_group_id}. Member NOT deleted from system."
            else:
                 message = f"Member {member_id_to_delete} was not associated with Group {our_group_id}. No mapping deleted."

        # 5. Commit Transaction
        conn.commit()
        current_app.logger.info(f"DB transaction committed for deletion task regarding MemberID {member_id_to_delete}.")

        return jsonify({
            "message": message,
            "deleted_from_login": deleted_from_login,
            "deleted_from_members": deleted_from_members,
            "deleted_from_mapping_for_this_group": deleted_from_mapping
            }), 200 # OK status for successful operation

    except mysql.connector.Error as db_err:
        current_app.logger.error(f"Database Error during Task 3 execution for MemberID {member_id_to_delete}: {db_err}")
        if conn: conn.rollback(); current_app.logger.info("DB transaction rolled back due to DB error.")
        return jsonify({"error": "Database error occurred during deletion", "details": str(db_err)}), 500
    except Exception as e:
        current_app.logger.error(f"Unexpected error during Task 3 for MemberID {member_id_to_delete}: {e}", exc_info=True)
        if conn: conn.rollback(); current_app.logger.info("DB transaction rolled back due to unexpected error.")
        return jsonify({"error": "An internal server error occurred during deletion", "details": str(e)}), 500
    finally:
        # Ensure cursor and connection are always closed
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()
        
# --- Route for Task 7: Get Members for OUR Group ---
@members_bp.route('/members/my_group', methods=['GET'])
@token_required # Require login to see group members
def get_my_group_members(current_user_id, current_user_role):
    """Fetches members belonging to the group specified in the config."""
    target_group_id = current_app.config.get('GROUP_ID') # Get group ID from config
    current_app.logger.info(f"Request: Get members for Group ID: {target_group_id} by User ID: {current_user_id}")

    # RBAC: Decide who can see the group list. Maybe any member of the group? Or just Admin/Coach?
    # For now, let's allow any logged-in user (decorator handles login).
    # Add specific role checks here if needed:
    # allowed_roles = ['admin', 'Coach', 'Player', ...]
    # if current_user_role not in allowed_roles:
    #     return jsonify({"error": "Insufficient privileges to view group members"}), 403

    conn = None; cursor = None
    try:
        conn = get_cims_db_connection()
        if not conn: return jsonify({"error": "Database connection failed"}), 500
        cursor = conn.cursor(dictionary=True)

        # SQL to get members belonging to the specific group ID
        # Ensure table/column names match: members (ID, UserName, emailID, DoB), MemberGroupMapping (MemberID, GroupID)
        sql_select_group_members = """
            SELECT m.ID, m.UserName, m.emailID, m.DoB
            FROM members m
            JOIN MemberGroupMapping mgm ON m.ID = mgm.MemberID
            WHERE mgm.GroupID = %s
            ORDER BY m.UserName
        """
        cursor.execute(sql_select_group_members, (target_group_id,))
        members_list = cursor.fetchall()

        current_app.logger.info(f"Retrieved {len(members_list)} members for Group ID: {target_group_id}")
        return jsonify(members_list), 200

    except mysql.connector.Error as db_err:
         # Handle potential "Table doesn't exist" if MemberGroupMapping name is wrong
         if db_err.errno == 1146:
              current_app.logger.error(f"DB Error: Table 'MemberGroupMapping' (or related) likely doesn't exist or name is wrong: {db_err}")
              return jsonify({"error": "Database configuration error finding group members.", "details": str(db_err)}), 500
         current_app.logger.error(f"Database Error getting group members: {db_err}")
         return jsonify({"error": "Database error occurred", "details": str(db_err)}), 500
    except Exception as e:
        current_app.logger.error(f"Unexpected error getting group members: {e}", exc_info=True)
        return jsonify({"error": "Server error occurred"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()
        
# --- Route for Task 7: Update Member Details (Admin Only) ---
@members_bp.route('/admin/members/<int:member_id_to_update>', methods=['PUT'])
@token_required
def update_member_admin(current_user_id, current_user_role, member_id_to_update):
    """Updates member details in the CIMS members table. Requires Admin role."""
    current_app.logger.info(f"Request: Update Member ID: {member_id_to_update} by Admin ID: {current_user_id}")

    # 1. RBAC Check
    if current_user_role != 'admin':
        return jsonify({"error": "Admin privileges required to update members"}), 403

    # 2. Get Data from Request Body
    try:
        data = request.get_json()
        if not data: return jsonify({"error": "Missing JSON body"}), 400

        # Fields allowed to be updated (adjust as needed)
        # Typically ID is not updated. Maybe Role is updated via a separate endpoint?
        username = data.get('UserName')
        email = data.get('emailID')
        dob_str = data.get('DoB') # Expect YYYY-MM-DD

        # Check that at least one field is provided
        if not any([username, email, dob_str]):
            return jsonify({"error": "No update fields provided (UserName, emailID, DoB)"}), 400

        # Validate Date if provided
        dob = None
        if dob_str:
            try:
                dob = datetime.date.fromisoformat(dob_str)
            except ValueError:
                return jsonify({"error": "Invalid date format for DoB. Use YYYY-MM-DD."}), 400

    except Exception as e:
        current_app.logger.error(f"Error parsing update member request JSON: {e}")
        return jsonify({"error": "Invalid JSON data"}), 400

    # 3. Database Update Operation
    conn = None; cursor = None
    try:
        conn = get_cims_db_connection()
        if not conn: return jsonify({"error": "Database connection failed"}), 500
        cursor = conn.cursor()

        # Build dynamic UPDATE statement
        update_fields = []
        update_values = []
        if username:
            update_fields.append("UserName = %s")
            update_values.append(username)
        if email:
            update_fields.append("emailID = %s")
            update_values.append(email)
        if dob:
            update_fields.append("DoB = %s")
            update_values.append(dob)

        if not update_fields: # Should be caught earlier
            return jsonify({"error": "No valid fields provided for update"}), 400

        update_values.append(member_id_to_update) # Add ID for WHERE clause

        sql_update = f"UPDATE members SET {', '.join(update_fields)} WHERE ID = %s"

        cursor.execute(sql_update, tuple(update_values))

        if cursor.rowcount == 0:
            return jsonify({"error": f"Member ID {member_id_to_update} not found"}), 404

        conn.commit()
        current_app.logger.info(f"Admin {current_user_id} updated Member ID: {member_id_to_update}")

        # Optionally fetch and return updated member data
        cursor.execute("SELECT ID, UserName, emailID, DoB FROM members WHERE ID = %s", (member_id_to_update,))
        updated_member = cursor.fetchone()

        return jsonify({
            "message": "Member updated successfully",
            "member": updated_member
        }), 200

    except mysql.connector.Error as db_err:
        if conn: conn.rollback()
        # Handle potential unique constraint errors (e.g., emailID if it's unique)
        if db_err.errno == 1062:
             return jsonify({"error": "Update failed: Duplicate value detected (e.g., email already exists).", "details": str(db_err)}), 409
        current_app.logger.error(f"DB Error updating member {member_id_to_update}: {db_err}")
        return jsonify({"error": "DB error", "details": str(db_err)}), 500
    except Exception as e:
        if conn: conn.rollback()
        current_app.logger.error(f"Error updating member {member_id_to_update}: {e}", exc_info=True)
        return jsonify({"error": "Server error"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()
