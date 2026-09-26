"""Coordinate fresh file publication with a DB transaction (not a distributed commit)."""
from pathlib import Path


def publish_staged(staged_path, destination, *, db_write=None):
    """Publish a same-volume staged file/directory, restoring it on ordinary failure.

    db_write(conn) must neither commit nor publish files. Existing nonempty output
    is never replaced. After process/power loss or an uncertain remote COMMIT,
    reconcile the database and files explicitly; two resources are not atomic.
    """
    staged, output = Path(staged_path), Path(destination)
    if staged.is_symlink() or output.is_symlink() or not staged.exists():
        raise ValueError("Publication requires a real staged file/directory and a fresh destination")
    was_empty = output.exists() and output.is_dir() and not any(output.iterdir())
    if output.exists() and not was_empty:
        raise ValueError("Publication refuses existing output; choose a fresh path")
    published = False

    def publish():
        nonlocal published
        if was_empty:
            output.rmdir()  # Only the explicitly verified empty destination.
        staged.rename(output)
        published = True

    if db_write is None:
        publish()
        return output
    try:
        import db
        with db.connection() as conn:
            db_write(conn)
            publish()
    except BaseException as exc:
        try:
            if published:
                output.rename(staged)  # Restore only the artifact this call published.
            if was_empty and not output.exists():
                output.mkdir()
        except OSError:
            raise RuntimeError("Database/file publication failed and file restoration failed; reconcile both stores before retrying") from None
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        # Do not propagate raw connection/SQL diagnostics containing credentials/data.
        raise RuntimeError(f"Database/file publication failed ({type(exc).__name__}); staged output restored. Verify database commit outcome before retrying.") from None
    return output
