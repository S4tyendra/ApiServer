from .db_utils import create_initial_admin, get_admin_collection, get_blog_collection

async def test_init_db():
    # Create initial admin
    success = await create_initial_admin()
    if success:
        print("Initial admin created successfully")
    else:
        print("Initial admin already exists")
    
    # Verify admin exists
    admin_collection = await get_admin_collection()
    admin = await admin_collection.find_one({"email": "satya@devh.in"})
    if admin:
        print(f"Found admin: {admin['name']} with role {admin['role']}")
    else:
        print("Admin not found!")

