-- Enable pgcrypto for gen_random_uuid
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  username text UNIQUE NOT NULL,
  email text UNIQUE NOT NULL,
  password_hash text NOT NULL,
  plan text NOT NULL CHECK (plan IN ('basic','premium')),
  created_at timestamptz NOT NULL DEFAULT now(),
  last_login timestamptz
);

CREATE TABLE IF NOT EXISTS clients (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name text NOT NULL,
  email text,
  phone text,
  address text,
  notes text,
  favorite boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (user_id, name)
);
CREATE INDEX IF NOT EXISTS idx_clients_user_name ON clients(user_id, name);

CREATE TABLE IF NOT EXISTS operations (
  id bigserial PRIMARY KEY,
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  client_id uuid NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  op_code text,
  source text NOT NULL CHECK (source IN ('manual','excel','pdf','grouped')),
  currency char(3) DEFAULT 'USD',
  total_value numeric(14,2) DEFAULT 0,
  extra jsonb DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_ops_user_created_desc ON operations(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ops_user_client_created ON operations(user_id, client_id, created_at DESC);

CREATE TABLE IF NOT EXISTS operation_items (
  id bigserial PRIMARY KEY,
  operation_id bigint NOT NULL REFERENCES operations(id) ON DELETE CASCADE,
  ncm varchar(10) NOT NULL,
  description text NOT NULL,
  origin char(3) NOT NULL,
  quantity numeric(14,3) NOT NULL,
  unit_value numeric(14,2) NOT NULL,
  unit_weight numeric(14,3) NOT NULL,
  extra jsonb DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_items_op ON operation_items(operation_id);
CREATE INDEX IF NOT EXISTS idx_items_ncm ON operation_items(ncm);

CREATE TABLE IF NOT EXISTS ncm_notes (
  id bigserial PRIMARY KEY,
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  client_id uuid REFERENCES clients(id) ON DELETE CASCADE,
  ncm varchar(10) NOT NULL,
  note text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_notes_user_ncm ON ncm_notes(user_id, ncm);


