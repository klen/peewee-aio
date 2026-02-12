DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'test') THEN
      CREATE ROLE test LOGIN PASSWORD 'test';
   END IF;
END
$$;

SELECT 'CREATE DATABASE tests OWNER test'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'tests')
\gexec
