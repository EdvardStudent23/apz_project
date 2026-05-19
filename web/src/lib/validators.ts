// Validation rules mirrored from services/auth/src/routes/schemas.py.
// Keep these in sync — the server is the source of truth, this is just
// fast-feedback for the user.

const USERNAME_RE = /^[a-zA-Z0-9_]+$/;
const SPECIAL_RE = /[!@#$%^&*()\-_=+\[\]{};:'",.<>/?\\|`~]/;
const WHITESPACE_RE = /\s/;

const RESERVED_USERNAMES = new Set([
  'root',
  'system',
  'official',
  'nanobank',
  'bank',
  'service',
  'noreply',
  'postmaster',
  'webmaster',
  'abuse',
  'null',
  'undefined',
  'anonymous',
]);

const COMMON_PASSWORDS = new Set([
  'password',
  'password1',
  'password123',
  'passw0rd',
  'qwerty',
  'qwerty123',
  'letmein',
  'welcome',
  'welcome1',
  'iloveyou',
  'admin123',
  'abc12345',
  '12345678',
  '123456789',
  '1234567890',
  '11111111',
  '00000000',
  'abcd1234',
  'monkey123',
  'dragon123',
  'football',
]);

export function validateUsername(raw: string): string | null {
  const v = raw.trim().toLowerCase();
  if (v.length < 3) return 'Username must be at least 3 characters.';
  if (v.length > 50) return 'Username must be at most 50 characters.';
  if (!USERNAME_RE.test(v)) return 'Username can only contain letters, digits and underscore.';
  if (/^\d/.test(v)) return 'Username must not start with a digit.';
  if (v.startsWith('_') || v.endsWith('_'))
    return 'Username must not start or end with an underscore.';
  if (/__/.test(v)) return 'Username must not contain consecutive underscores.';
  if (RESERVED_USERNAMES.has(v)) return 'This username is reserved, please choose another.';
  return null;
}

export function validateEmail(raw: string): string | null {
  const v = raw.trim();
  if (!v) return 'Email is required.';
  if (v.length > 254) return 'Email is too long.';
  // RFC-ish: requires local@domain.tld
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) return 'Please enter a valid email address.';
  return null;
}

export function validatePassword(
  password: string,
  context: { username?: string; email?: string } = {},
): string | null {
  if (password.length < 8) return 'Password must be at least 8 characters.';
  if (password.length > 128) return 'Password must be at most 128 characters.';
  if (WHITESPACE_RE.test(password)) return 'Password must not contain whitespace.';
  if (!/[A-Z]/.test(password)) return 'Password must contain an uppercase letter.';
  if (!/[a-z]/.test(password)) return 'Password must contain a lowercase letter.';
  if (!/\d/.test(password)) return 'Password must contain a digit.';
  if (!SPECIAL_RE.test(password))
    return 'Password must contain a special character (e.g. ! @ # $ % …).';
  if (new Set(password).size < 4) return 'Password must use at least 4 distinct characters.';
  if (COMMON_PASSWORDS.has(password.toLowerCase()))
    return 'This password is too common, please choose another.';

  const username = context.username?.trim().toLowerCase();
  if (username && username.length >= 3 && password.toLowerCase().includes(username))
    return 'Password must not contain your username.';

  const localPart = context.email?.split('@')[0]?.trim().toLowerCase();
  if (localPart && localPart.length >= 3 && password.toLowerCase().includes(localPart))
    return 'Password must not contain the local part of your email.';

  return null;
}
