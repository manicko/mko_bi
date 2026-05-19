import { describe, it, expect } from 'vitest'
import {
  UserRole,
  DashboardPermission,
  GraphType,
  FilterType,
  RegistrationStatus,
  UploadMode,
  ProcessingStatus,
  FileUploadStatus,
} from '../enums'

describe('UserRole', () => {
  it('has correct values', () => {
    expect(UserRole.ADMIN).toBe('admin')
    expect(UserRole.EDITOR).toBe('editor')
    expect(UserRole.VIEWER).toBe('viewer')
  })

  it('has exactly 3 roles', () => {
    expect(Object.keys(UserRole)).toHaveLength(3)
  })
})

describe('DashboardPermission', () => {
  it('has correct values', () => {
    expect(DashboardPermission.VIEW).toBe('view')
    expect(DashboardPermission.EDIT).toBe('edit')
    expect(DashboardPermission.ADMIN).toBe('admin')
  })

  it('has exactly 3 permissions', () => {
    expect(Object.keys(DashboardPermission)).toHaveLength(3)
  })
})

describe('GraphType', () => {
  it('has correct values', () => {
    expect(GraphType.BAR).toBe('bar')
    expect(GraphType.LINE).toBe('line')
    expect(GraphType.PIE).toBe('pie')
    expect(GraphType.TABLE).toBe('table')
  })

  it('has exactly 4 types', () => {
    expect(Object.keys(GraphType)).toHaveLength(4)
  })
})

describe('FilterType', () => {
  it('has correct values', () => {
    expect(FilterType.SELECT).toBe('select')
    expect(FilterType.MULTISELECT).toBe('multiselect')
    expect(FilterType.RANGE).toBe('range')
    expect(FilterType.DATE).toBe('date')
  })

  it('has exactly 4 types', () => {
    expect(Object.keys(FilterType)).toHaveLength(4)
  })
})

describe('RegistrationStatus', () => {
  it('has correct values', () => {
    expect(RegistrationStatus.PENDING).toBe('pending')
    expect(RegistrationStatus.APPROVED).toBe('approved')
    expect(RegistrationStatus.REJECTED).toBe('rejected')
  })
})

describe('UploadMode', () => {
  it('has correct values', () => {
    expect(UploadMode.OVERWRITE).toBe('overwrite')
    expect(UploadMode.APPEND).toBe('append')
  })
})

describe('ProcessingStatus', () => {
  it('has correct values', () => {
    expect(ProcessingStatus.STARTED).toBe('started')
    expect(ProcessingStatus.UPLOADED).toBe('uploaded')
    expect(ProcessingStatus.PROCESSING).toBe('processing')
    expect(ProcessingStatus.SUCCESS).toBe('success')
    expect(ProcessingStatus.FAILED).toBe('failed')
    expect(ProcessingStatus.COMPLETED).toBe('completed')
  })

  it('has exactly 6 statuses', () => {
    expect(Object.keys(ProcessingStatus)).toHaveLength(6)
  })
})

describe('FileUploadStatus', () => {
  it('has correct values', () => {
    expect(FileUploadStatus.PENDING).toBe('pending')
    expect(FileUploadStatus.UPLOADING).toBe('uploading')
    expect(FileUploadStatus.SUCCESS).toBe('success')
    expect(FileUploadStatus.ERROR).toBe('error')
  })
})
