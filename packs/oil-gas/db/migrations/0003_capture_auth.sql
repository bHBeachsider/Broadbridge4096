-- Auth.js email-only capture authentication. No ORM migrations or raw magic-link tokens.
CREATE TABLE broadbridge.auth_users (
    id text PRIMARY KEY DEFAULT gen_random_uuid()::text,
    email text NOT NULL UNIQUE CHECK (email = lower(btrim(email)) AND email <> ''),
    email_verified timestamptz,
    name text,
    image text,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE broadbridge.auth_verification_tokens (
    identifier text NOT NULL CHECK (identifier = lower(btrim(identifier)) AND identifier <> ''),
    token text NOT NULL CHECK (token ~ '^[0-9a-f]{64}$'),
    expires timestamptz NOT NULL,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (identifier, token),
    CHECK (expires > created_at AND expires <= created_at + interval '15 minutes')
);
CREATE INDEX auth_verification_tokens_expiry ON broadbridge.auth_verification_tokens(expires);

CREATE TABLE broadbridge.auth_email_cooldowns (
    identifier text PRIMARY KEY CHECK (identifier = lower(btrim(identifier)) AND identifier <> ''),
    last_issued_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
