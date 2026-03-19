# Create Migration

Generate and apply a Django database migration after model changes.

## Arguments
$ARGUMENTS — Optional: short snake_case description of the change
(e.g., `add_embedding_field`, `add_document_chunk_model`)

## Steps

1. **Read** `documents/models.py` to understand what changed.

2. **Check the latest migration**:
   ```bash
   ls documents/migrations/
   ```

3. **Generate the migration**:
   ```bash
   # With descriptive name
   python manage.py makemigrations documents --name "$ARGUMENTS"

   # Or auto-named if no argument
   python manage.py makemigrations documents
   ```

4. **Review** the generated migration file:
   - Correct fields added / removed / altered
   - Correct dependency on the previous migration
   - No unintended `RunSQL` or data migration needed
   - If data migration IS needed, flag this explicitly before proceeding

5. **Apply the migration**:
   ```bash
   python manage.py migrate
   ```

6. **Docker path**:
   ```bash
   docker-compose exec web python manage.py makemigrations documents --name "$ARGUMENTS"
   docker-compose exec web python manage.py migrate
   ```

7. Output the migration filename created and confirm it applied successfully.

## Special Cases

- **pgvector `VectorField`**: ensure the `vector` extension is enabled first via
  a migration with `migrations.RunSQL("CREATE EXTENSION IF NOT EXISTS vector")`.
  This must be a separate migration that runs before the field migration.

- **Making nullable field non-nullable**: always add a `default=` to the field
  definition first, then remove it in a follow-up migration after backfilling.

- **Never edit** migration files already committed to `main`.
