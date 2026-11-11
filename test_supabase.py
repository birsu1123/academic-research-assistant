from database.supabase import get_supabase_client

supabase = get_supabase_client()

response = (
    supabase.table("collections")
    .select("id")
    .limit(1)
    .execute()
)

print("Supabase query successful!")
print(response.data)