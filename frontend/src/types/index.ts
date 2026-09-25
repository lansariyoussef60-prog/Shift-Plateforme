export type Role = 'ADMIN' | 'PM' | 'OCP' | 'OCVP' | 'OC';

export type User = {
  id: string;
  full_name: string;
  email: string;
  role: Role;
  department_id?: string | null;
  manager_id?: string | null;
  is_active: boolean;
};

export type Project = {
  id: string;
  name: string;
  start_date?: string | null;
  end_date?: string | null;
  is_active: boolean;
  created_at: string;
};

export type Department = {
  id: string;
  name: string;
  project_id: string;
  created_at: string;
};

export type Partner = {
  id: string;
  company_name: string;
  normalized_name: string;
  industry?: string | null;
  contact_person?: string | null;
  email?: string | null;
  phone?: string | null;
  address?: string | null;
  city?: string | null;
  website?: string | null;
  partner_type: string;
  status: string;
  last_contact_date?: string | null;
  last_contacted_by_id?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
};

export type Contact = {
  id: string;
  partner_id?: string;
  speaker_id?: string;
  user_id?: string | null;
  project_id?: string | null;
  contact_method: string;
  result?: string | null;
  notes?: string | null;
  follow_up_date?: string | null;
  created_at: string;
};

export type Collaboration = {
  id: string;
  partner_id: string;
  project_id: string;
  title: string;
  amount_value?: number | null;
  currency?: string | null;
  confirmed_by_id?: string | null;
  confirmed_at: string;
  notes?: string | null;
};

export type Speaker = {
  id: string;
  name: string;
  normalized_name: string;
  organization?: string | null;
  position?: string | null;
  email?: string | null;
  phone?: string | null;
  linkedin?: string | null;
  topic?: string | null;
  status: string;
  contacted_by_id?: string | null;
  contact_date?: string | null;
  confirmation_status?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
};

export type TargetList = {
  id: string;
  name: string;
  owner_id: string;
  department_id?: string | null;
  project_id: string;
  created_at: string;
};

export type TargetItem = {
  id: string;
  target_list_id: string;
  partner_id: string;
  status: string;
  added_by_id?: string | null;
  added_at: string;
  partner: Partner;
};

export type Task = {
  id: string;
  title: string;
  description?: string | null;
  created_by_id?: string | null;
  assigned_to_id: string;
  priority: string;
  status: string;
  deadline?: string | null;
  completed_at?: string | null;
  created_at: string;
  updated_at: string;
};

export type Goal = {
  id: string;
  title: string;
  description?: string | null;
  target_value: number;
  current_value: number;
  unit?: string | null;
  scope: string;
  project_id: string;
  department_id?: string | null;
  user_id?: string | null;
  responsible_id?: string | null;
  deadline?: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export type MktItem = {
  id: string;
  title: string;
  description?: string | null;
  start_date: string;
  end_date?: string | null;
  responsible_id?: string | null;
  department_id?: string | null;
  project_id: string;
  status: string;
  priority: string;
  related_task_id?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
};

export type Activity = {
  id: string;
  actor_id?: string | null;
  action: string;
  entity_type: string;
  entity_id?: string | null;
  description?: string | null;
  created_at: string;
};

export type Invite = {
  id: string;
  email: string;
  role: Role;
  department_id?: string | null;
  manager_id?: string | null;
  expires_at: string;
  used_at?: string | null;
  created_at: string;
  invite_link?: string | null;
};

export type RegisterResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};
