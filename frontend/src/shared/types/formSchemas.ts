import { z } from 'zod'

const BLOCKED_DOMAINS = ['tempmail.com', 'throwawaymail.com']

// Login form schema
export const loginSchema = z.object({
  email: z.string().email('Invalid email format'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
})

export type LoginFormData = z.infer<typeof loginSchema>

// Registration form schema
export const registerSchema = z.object({
  email: z
    .string()
    .email('Invalid email format')
    .refine((email) => {
      const domain = email.split('@')[1]
      return domain && !BLOCKED_DOMAINS.includes(domain)
    }, 'This email domain is not allowed'),
})

export type RegisterFormData = z.infer<typeof registerSchema>

// Dashboard creation schema
export const createDashboardSchema = z.object({
  name: z.string().min(1, 'Dashboard name is required').max(100, 'Dashboard name is too long'),
  description: z.string().max(500, 'Description is too long').optional(),
})

export type CreateDashboardFormData = z.infer<typeof createDashboardSchema>

// Dashboard update schema
export const updateDashboardSchema = z.object({
  name: z.string().min(1, 'Dashboard name is required').max(100, 'Dashboard name is too long').optional(),
  description: z.string().max(500, 'Description is too long').optional(),
})

export type UpdateDashboardFormData = z.infer<typeof updateDashboardSchema>

// Grant dashboard access schema
export const grantAccessSchema = z.object({
  user_id: z.string().uuid('Invalid user ID'),
  permission: z.enum(['view', 'edit', 'admin']),
})

export type GrantAccessFormData = z.infer<typeof grantAccessSchema>
