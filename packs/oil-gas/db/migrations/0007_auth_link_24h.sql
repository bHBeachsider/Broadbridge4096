-- Expand the bound for newly issued links; do not change existing token rows.
-- Applied before the provider/adapter starts requesting 24-hour links.
ALTER TABLE broadbridge.auth_verification_tokens
    DROP CONSTRAINT auth_verification_tokens_check,
    ADD CONSTRAINT auth_verification_tokens_expiry_check
        CHECK (expires > created_at AND expires <= created_at + interval '24 hours');
