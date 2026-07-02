"""Reject throwaway / disposable email addresses so temporary-email spam can't get
through signup or checkout. Two layers:

  1. a bundled blocklist of known disposable domains (data/disposable_domains.txt),
     which also matches subdomains of any listed domain, and
  2. a best-effort live DNS check that the domain can actually receive mail (has an
     MX or A record) — this never blocks on a transient DNS error, only on a
     definitive "this domain can't receive mail".

Combined with the mandatory email-verification code, this stops the common
temp-mail tricks: a fake domain fails the DNS check, a throwaway domain is on the
blocklist, and a real-but-not-yours address never receives the code.
"""
import os

_DIR = os.path.dirname(os.path.abspath(__file__))
_BLOCKLIST_PATH = os.path.join(_DIR, "data", "disposable_domains.txt")


def _load_blocklist():
    domains = set()
    try:
        with open(_BLOCKLIST_PATH, encoding="utf-8") as fh:
            for line in fh:
                d = line.strip().lower()
                if d and not d.startswith("#"):
                    domains.add(d)
    except OSError:
        pass
    return domains


_BLOCK = _load_blocklist()


def domain_of(email: str) -> str:
    email = (email or "").strip().lower()
    return email.rsplit("@", 1)[-1] if "@" in email else ""


def is_disposable(email: str) -> bool:
    """True if the address is on the disposable blocklist (incl. subdomains)."""
    d = domain_of(email)
    if not d:
        return False
    if d in _BLOCK:
        return True
    parts = d.split(".")
    # foo.mailinator.com → also matches "mailinator.com"
    for i in range(1, len(parts) - 1):
        if ".".join(parts[i:]) in _BLOCK:
            return True
    return False


def has_mail_server(domain: str) -> bool:
    """Best-effort: True unless we can DEFINITIVELY prove the domain can't receive
    mail (no MX and no A, or the domain doesn't exist). Any transient/uncertain
    result returns True so we never block a legitimate address."""
    if not domain:
        return True
    try:
        import dns.resolver  # dnspython
    except Exception:
        return True  # not installed → skip the live check gracefully
    try:
        answers = dns.resolver.resolve(domain, "MX")
        if len(answers) > 0:
            return True
    except dns.resolver.NXDOMAIN:
        return False
    except dns.resolver.NoAnswer:
        pass
    except Exception:
        return True  # timeout / SERVFAIL / no nameservers → don't block
    # No MX record — some domains still accept mail on their A host.
    try:
        dns.resolver.resolve(domain, "A")
        return True
    except dns.resolver.NXDOMAIN:
        return False
    except Exception:
        return True


def check(email: str) -> str:
    """Return a user-facing error string if the email should be rejected, else ''."""
    d = domain_of(email)
    if not d or "." not in d:
        return "Please enter a valid email address."
    if is_disposable(email):
        return "Temporary / disposable email addresses aren't allowed. Please use a permanent email you can receive mail at."
    if not has_mail_server(d):
        return "That email domain can't receive mail. Please double-check the address."
    return ""
