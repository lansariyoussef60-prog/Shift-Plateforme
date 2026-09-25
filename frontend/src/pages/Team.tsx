import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Copy, MailPlus, RefreshCw, UserPlus, } from 'lucide-react';
import { Button, Card, Modal, Field, Input, Select, Table, Badge, Empty, ErrorBox } from '../components/UI';
import { del, errMsg, get, patch, post } from '../lib/api';
import type { Department, Invite, Project, Role, User } from '../types';
import { Page } from '../components/UI';

const roles: Role[] = ['PM', 'OCP', 'OCVP', 'OC'];

const managerRoles: Record<Role, Role[]> = {
  ADMIN: [],
  PM: [],
  OCP: ['PM'],
  OCVP: ['OCP'],
  OC: ['OCVP'],
};

function inviteStatus(invite: Invite) {
  if (invite.used_at) return { label: 'USED / REVOKED', tone: 'neutral' as const };
  if (new Date(invite.expires_at).getTime() <= Date.now()) return { label: 'EXPIRED', tone: 'danger' as const };
  return { label: 'PENDING', tone: 'success' as const };
}

function formatDate(value?: string | null) {
  if (!value) return '—';
  return new Date(value).toLocaleString();
}

export default function Team({ user }: { user: User }) {
  const qc = useQueryClient();
  const usersQuery = useQuery<User[]>({ queryKey: ['users'], queryFn: () => get('/users') });
  const projectsQuery = useQuery<Project[]>({ queryKey: ['projects'], queryFn: () => get('/projects') });
  const invitesQuery = useQuery<Invite[]>({
    queryKey: ['invites'],
    queryFn: () => get('/invites'),
    enabled: user.role === 'ADMIN',
  });

  const [openInvite, setOpenInvite] = useState(false);
  const [email, setEmail] = useState('');
  const [role, setRole] = useState<Role>('OC');
  const [projectId, setProjectId] = useState('');
  const [departmentId, setDepartmentId] = useState('');
  const [managerId, setManagerId] = useState('');
  const [formError, setFormError] = useState('');
  const [createdInvite, setCreatedInvite] = useState<Invite | null>(null);
  const [copied, setCopied] = useState(false);

  const departmentsQuery = useQuery<Department[]>({
    queryKey: ['departments', projectId],
    queryFn: () => get('/departments', { project_id: projectId }),
    enabled: Boolean(projectId),
  });

  const eligibleManagers = useMemo(() => {
    const wanted = managerRoles[role];
    if (!wanted.length) return [];
    return (usersQuery.data ?? []).filter((candidate) => candidate.is_active && wanted.includes(candidate.role));
  }, [role, usersQuery.data]);

  const createInvite = useMutation({
    mutationFn: () =>
      post<Invite>('/invites', {
        email: email.trim().toLowerCase(),
        role,
        department_id: departmentId || null,
        manager_id: managerId || null,
      }),
    onSuccess: (invite) => {
      setCreatedInvite(invite);
      qc.invalidateQueries({ queryKey: ['invites'] });
      setFormError('');
    },
    onError: (error) => setFormError(errMsg(error)),
  });

  const revokeInvite = useMutation({
    mutationFn: (id: string) => del<Invite>(`/invites/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['invites'] }),
    onError: (error) => window.alert(errMsg(error)),
  });

  const resetInvite = () => {
    setOpenInvite(false);
    setEmail('');
    setRole('OC');
    setProjectId('');
    setDepartmentId('');
    setManagerId('');
    setFormError('');
    setCreatedInvite(null);
    setCopied(false);
  };

  const copyInvite = async () => {
    if (!createdInvite?.invite_link) return;
    await navigator.clipboard.writeText(createdInvite.invite_link);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
  };

  const changeManager = async (member: User, value: string) => {
    try {
      await patch(`/users/${member.id}/manager`, { manager_id: value || null });
      qc.invalidateQueries({ queryKey: ['users'] });
    } catch (error) {
      window.alert(errMsg(error));
    }
  };

  return (
    <Page
      title="Team & Users"
      subtitle="Manage the PM → OCP → OCVP → OC hierarchy and invite new members."
      actions={
        user.role === 'ADMIN' ? (
          <Button onClick={() => setOpenInvite(true)}>
            <MailPlus size={15} style={{ verticalAlign: 'middle', marginRight: 6 }} />
            Invite member
          </Button>
        ) : null
      }
    >
      <Card>
        {usersQuery.isLoading ? (
          'Loading…'
        ) : !usersQuery.data?.length ? (
          <Empty text="No users found." />
        ) : (
          <Table heads={['Member', 'Role', 'Manager', 'Department', 'Status', 'Actions']}>
            {usersQuery.data.map((member) => {
              const managers = usersQuery.data.filter(
                (candidate) =>
                  candidate.id !== member.id &&
                  candidate.is_active &&
                  managerRoles[member.role].includes(candidate.role),
              );

              return (
                <tr key={member.id}>
                  <td>
                    <b>{member.full_name}</b>
                    <small>{member.email}</small>
                  </td>
                  <td><Badge>{member.role}</Badge></td>
                  <td>
                    <Select
                      value={member.manager_id || ''}
                      onChange={(event) => changeManager(member, event.target.value)}
                      disabled={member.role === 'ADMIN' || member.role === 'PM'}
                    >
                      <option value="">None</option>
                      {managers.map((manager) => (
                        <option key={manager.id} value={manager.id}>
                          {manager.full_name} · {manager.role}
                        </option>
                      ))}
                    </Select>
                  </td>
                  <td>{member.department_id || '—'}</td>
                  <td><Badge tone={member.is_active ? 'success' : 'danger'}>{member.is_active ? 'ACTIVE' : 'INACTIVE'}</Badge></td>
                  <td>
                    {user.role === 'ADMIN' && member.is_active && member.id !== user.id && (
                      <Button
                        variant="danger"
                        onClick={async () => {
                          if (!window.confirm(`Deactivate ${member.full_name}?`)) return;
                          try {
                            await patch(`/users/${member.id}/deactivate`);
                            qc.invalidateQueries({ queryKey: ['users'] });
                          } catch (error) {
                            window.alert(errMsg(error));
                          }
                        }}
                      >
                        Deactivate
                      </Button>
                    )}
                  </td>
                </tr>
              );
            })}
          </Table>
        )}
      </Card>

      {user.role === 'ADMIN' && (
        <Card>
          <div className="sectionhead">
            <div>
              <h2>Invitations</h2>
              <p className="muted">Every invitation is single-use and expires according to the backend configuration.</p>
            </div>
            <Button variant="secondary" onClick={() => invitesQuery.refetch()}>
              <RefreshCw size={14} style={{ verticalAlign: 'middle', marginRight: 5 }} />
              Refresh
            </Button>
          </div>

          {invitesQuery.isLoading ? (
            'Loading invitations…'
          ) : !invitesQuery.data?.length ? (
            <Empty text="No invitations have been created yet." />
          ) : (
            <Table heads={['Email', 'Role', 'Manager', 'Status', 'Expires', 'Created', 'Actions']}>
              {invitesQuery.data.map((invite) => {
                const status = inviteStatus(invite);
                const manager = usersQuery.data?.find((member) => member.id === invite.manager_id);
                return (
                  <tr key={invite.id}>
                    <td><b>{invite.email}</b></td>
                    <td><Badge>{invite.role}</Badge></td>
                    <td>{manager?.full_name || invite.manager_id || '—'}</td>
                    <td><Badge tone={status.tone}>{status.label}</Badge></td>
                    <td>{formatDate(invite.expires_at)}</td>
                    <td>{formatDate(invite.created_at)}</td>
                    <td>
                      {!invite.used_at && new Date(invite.expires_at).getTime() > Date.now() && (
                        <Button
                          variant="danger"
                          disabled={revokeInvite.isPending}
                          onClick={() => {
                            if (window.confirm(`Revoke the invitation for ${invite.email}?`)) revokeInvite.mutate(invite.id);
                          }}
                        >
                          Revoke
                        </Button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </Table>
          )}
        </Card>
      )}

      {openInvite && (
        <Modal title="Invite a SHIFT member" onClose={resetInvite}>
          {!createdInvite ? (
            <form
              onSubmit={(event) => {
                event.preventDefault();
                setFormError('');
                createInvite.mutate();
              }}
            >
              <div className="inviteintro">
                <div className="inviteicon"><UserPlus size={18} /></div>
                <div>
                  <b>Admin controls the hierarchy</b>
                  <p>The invited person will only choose their name and password. Their role, department and manager are fixed by this invitation.</p>
                </div>
              </div>

              <Field label="Email address">
                <Input
                  type="email"
                  required
                  value={email}
                  placeholder="member@aiesec.org"
                  onChange={(event) => setEmail(event.target.value)}
                />
              </Field>

              <div className="grid two">
                <Field label="Role">
                  <Select
                    value={role}
                    onChange={(event) => {
                      setRole(event.target.value as Role);
                      setManagerId('');
                    }}
                  >
                    {roles.map((item) => <option key={item} value={item}>{item}</option>)}
                  </Select>
                </Field>
                <Field label="Project for department">
                  <Select
                    value={projectId}
                    onChange={(event) => {
                      setProjectId(event.target.value);
                      setDepartmentId('');
                    }}
                  >
                    <option value="">No department</option>
                    {projectsQuery.data?.map((project) => <option key={project.id} value={project.id}>{project.name}</option>)}
                  </Select>
                </Field>
              </div>

              {projectId && (
                <Field label="Department">
                  <Select value={departmentId} onChange={(event) => setDepartmentId(event.target.value)}>
                    <option value="">No department</option>
                    {departmentsQuery.data?.map((department) => (
                      <option key={department.id} value={department.id}>{department.name}</option>
                    ))}
                  </Select>
                </Field>
              )}

              {managerRoles[role].length > 0 && (
                <Field label={`Manager (${managerRoles[role].join(' / ')})`}>
                  <Select required value={managerId} onChange={(event) => setManagerId(event.target.value)}>
                    <option value="">Select manager</option>
                    {eligibleManagers.map((manager) => (
                      <option key={manager.id} value={manager.id}>
                        {manager.full_name} · {manager.role}
                      </option>
                    ))}
                  </Select>
                </Field>
              )}

              {formError && <ErrorBox error={formError} />}

              <div className="modalactions">
                <Button variant="secondary" onClick={resetInvite}>Cancel</Button>
                <Button type="submit" disabled={createInvite.isPending}>
                  {createInvite.isPending ? 'Creating…' : 'Create invitation'}
                </Button>
              </div>
            </form>
          ) : (
            <div>
              <div className="successpanel">
                <div className="successdot">✓</div>
                <div>
                  <h3>Invitation created</h3>
                  <p>{createdInvite.email} can now use the generated registration link.</p>
                </div>
              </div>

              <Field label="Registration link">
                <div className="copyrow">
                  <Input readOnly value={createdInvite.invite_link || ''} />
                  <Button variant="secondary" onClick={copyInvite} disabled={!createdInvite.invite_link}>
                    <Copy size={15} style={{ verticalAlign: 'middle', marginRight: 5 }} />
                    {copied ? 'Copied' : 'Copy'}
                  </Button>
                </div>
              </Field>

              <div className="detailgrid">
                <div><span>Email</span><b>{createdInvite.email}</b></div>
                <div><span>Role</span><b>{createdInvite.role}</b></div>
                <div><span>Expires</span><b>{formatDate(createdInvite.expires_at)}</b></div>
                <div><span>Single use</span><b>Yes</b></div>
              </div>

              <div className="warningpanel">
                <h3>Important</h3>
                <p>Creating another invitation for this same email automatically invalidates the previous pending invitation.</p>
              </div>

              <div className="modalactions">
                <Button variant="secondary" onClick={resetInvite}>Close</Button>
                <Button onClick={() => { setCreatedInvite(null); setCopied(false); }}>Create another</Button>
              </div>
            </div>
          )}
        </Modal>
      )}
    </Page>
  );
}
