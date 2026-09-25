import { FormEvent, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { CheckCircle2, Eye, EyeOff, ShieldCheck, XCircle } from 'lucide-react';
import { Button, Card, Field, Input, ErrorBox } from '../components/UI';
import { errMsg, post, setAccess, setRefresh } from '../lib/api';
import type { RegisterResponse } from '../types';

function passwordChecks(password: string) {
  return {
    length: password.length >= 8,
    max: password.length <= 72,
  };
}

export default function Register({ onLogin }: { onLogin: () => Promise<void> | void }) {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token')?.trim() || '';

  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const checks = useMemo(() => passwordChecks(password), [password]);
  const mismatch = confirm.length > 0 && password !== confirm;
  const invalidToken = !token;

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setError('');

    if (invalidToken) return;
    if (name.trim().length < 2) {
      setError('Please enter your full name.');
      return;
    }
    if (!checks.length || !checks.max) {
      setError('Password must be between 8 and 72 characters.');
      return;
    }
    if (password !== confirm) {
      setError('Passwords do not match.');
      return;
    }

    setSubmitting(true);
    try {
      const response = await post<RegisterResponse>('/auth/register', {
        token,
        full_name: name.trim(),
        password,
      });

      // /auth/register returns the exact same token shape as /auth/login.
      setAccess(response.access_token);
      setRefresh(response.refresh_token);
      await onLogin();
      navigate('/', { replace: true });
    } catch (requestError) {
      setError(errMsg(requestError));
    } finally {
      setSubmitting(false);
    }
  };

  if (invalidToken) {
    return (
      <div className="auth">
        <Card className="authcard invalidinvite">
          <div className="authbrand">
            <div className="logo big">S</div>
            <h1>Invalid invitation</h1>
            <p>This registration link is missing its invitation token.</p>
          </div>
          <div className="invite-state dangerstate">
            <XCircle size={30} />
            <div>
              <b>This registration link is invalid</b>
              <span>Ask an Admin to create a new invitation for you.</span>
            </div>
          </div>
          <Button onClick={() => navigate('/login')}>Back to sign in</Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="auth">
      <Card className="authcard registercard">
        <div className="authbrand">
          <div className="logo big">S</div>
          <h1>Join SHIFT</h1>
          <p>Complete your invitation to activate your AIESEC account.</p>
        </div>

        <div className="invite-state validstate">
          <ShieldCheck size={24} />
          <div>
            <b>Invitation detected</b>
            <span>Your account permissions are already configured by an Admin.</span>
          </div>
        </div>

        <form onSubmit={submit} noValidate>
          <Field label="Full name">
            <Input
              required
              autoComplete="name"
              value={name}
              placeholder="Your full name"
              onChange={(event) => setName(event.target.value)}
            />
          </Field>

          <Field label="Password">
            <div className="passwordfield">
              <Input
                type={showPassword ? 'text' : 'password'}
                required
                minLength={8}
                maxLength={72}
                autoComplete="new-password"
                value={password}
                placeholder="At least 8 characters"
                onChange={(event) => setPassword(event.target.value)}
              />
              <button type="button" className="passwordtoggle" onClick={() => setShowPassword((value) => !value)} aria-label={showPassword ? 'Hide password' : 'Show password'}>
                {showPassword ? <EyeOff size={17} /> : <Eye size={17} />}
              </button>
            </div>
          </Field>

          <div className="passwordrules">
            <span className={checks.length ? 'rule ok' : 'rule'}>
              {checks.length ? <CheckCircle2 size={13} /> : <XCircle size={13} />} At least 8 characters
            </span>
            <span className={checks.max ? 'rule ok' : 'rule'}>
              {checks.max ? <CheckCircle2 size={13} /> : <XCircle size={13} />} Maximum 72 characters
            </span>
          </div>

          <Field label="Confirm password">
            <div className="passwordfield">
              <Input
                type={showConfirm ? 'text' : 'password'}
                required
                autoComplete="new-password"
                value={confirm}
                placeholder="Repeat your password"
                onChange={(event) => setConfirm(event.target.value)}
              />
              <button type="button" className="passwordtoggle" onClick={() => setShowConfirm((value) => !value)} aria-label={showConfirm ? 'Hide confirmation password' : 'Show confirmation password'}>
                {showConfirm ? <EyeOff size={17} /> : <Eye size={17} />}
              </button>
            </div>
          </Field>

          {mismatch && <div className="fieldhint dangertext">Passwords do not match.</div>}
          {error && <ErrorBox error={error} />}

          <Button type="submit" disabled={submitting || mismatch || !checks.length || !checks.max}>
            {submitting ? 'Creating account…' : 'Create account'}
          </Button>
        </form>

        <p className="securitynote">Your email, role, department and manager come from the invitation and cannot be changed here.</p>
      </Card>
    </div>
  );
}
