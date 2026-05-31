import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { FileDropzone } from '../ui/FileDropzone'

// Mock react-dropzone
vi.mock('react-dropzone', () => ({
  useDropzone: vi.fn(),
}))

// Mock react-hot-toast
vi.mock('react-hot-toast', () => ({
  toast: {
    error: vi.fn(),
  },
  default: {
    error: vi.fn(),
  },
}))

import { useDropzone } from 'react-dropzone'

const mockOnFilesSelected = vi.fn()
const mockOnFileRemove = vi.fn()

const createDefaultFile = (name: string, size: number, type: string): File => {
  const file = new File([''], name, { type })
  Object.defineProperty(file, 'size', { value: size })
  return file
}

describe('FileDropzone', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders dropzone instruction text', () => {
    vi.mocked(useDropzone).mockReturnValue({
      getRootProps: vi.fn(() => ({})),
      getInputProps: vi.fn(() => ({})),
      isDragActive: false,
      isFocused: false,
      isDragAccept: false,
      isDragReject: false,
      isFileDialogActive: false,
      acceptedFiles: [],
      fileRejections: [],
      open: vi.fn(),
    } as unknown as ReturnType<typeof useDropzone>)

    render(
      <FileDropzone
        onFilesSelected={mockOnFilesSelected}
        onFileRemove={mockOnFileRemove}
        selectedFiles={[]}
      />
    )

    expect(screen.getByText(/drag & drop files here/i)).toBeInTheDocument()
    expect(screen.getByText(/only .csv and .csv.gz files are allowed/i)).toBeInTheDocument()
  })

  it('renders empty dropzone when no files selected', () => {
    vi.mocked(useDropzone).mockReturnValue({
      getRootProps: vi.fn(() => ({})),
      getInputProps: vi.fn(() => ({})),
      isDragActive: false,
      isFocused: false,
      isDragAccept: false,
      isDragReject: false,
      isFileDialogActive: false,
      acceptedFiles: [],
      fileRejections: [],
      open: vi.fn(),
    } as unknown as ReturnType<typeof useDropzone>)

    render(
      <FileDropzone
        onFilesSelected={mockOnFilesSelected}
        onFileRemove={mockOnFileRemove}
        selectedFiles={[]}
      />
    )

    // No file list items should be visible
    const fileItems = screen.queryAllByRole('listitem')
    expect(fileItems).toHaveLength(0)
  })

  it('renders selected files when provided', () => {
    const file = createDefaultFile('test.csv', 1024, 'text/csv')

    vi.mocked(useDropzone).mockReturnValue({
      getRootProps: vi.fn(() => ({})),
      getInputProps: vi.fn(() => ({})),
      isDragActive: false,
      isFocused: false,
      isDragAccept: false,
      isDragReject: false,
      isFileDialogActive: false,
      acceptedFiles: [],
      fileRejections: [],
      open: vi.fn(),
    } as unknown as ReturnType<typeof useDropzone>)

    render(
      <FileDropzone
        onFilesSelected={mockOnFilesSelected}
        onFileRemove={mockOnFileRemove}
        selectedFiles={[file]}
      />
    )

    expect(screen.getByText('test.csv')).toBeInTheDocument()
  })

  it('renders file size in KB format', () => {
    const file = createDefaultFile('test.csv', 1536, 'text/csv') // 1.5 KB

    vi.mocked(useDropzone).mockReturnValue({
      getRootProps: vi.fn(() => ({})),
      getInputProps: vi.fn(() => ({})),
      isDragActive: false,
      isFocused: false,
      isDragAccept: false,
      isDragReject: false,
      isFileDialogActive: false,
      acceptedFiles: [],
      fileRejections: [],
      open: vi.fn(),
    } as unknown as ReturnType<typeof useDropzone>)

    render(
      <FileDropzone
        onFilesSelected={mockOnFilesSelected}
        onFileRemove={mockOnFileRemove}
        selectedFiles={[file]}
      />
    )

    expect(screen.getByText(/1.50 kb/i)).toBeInTheDocument()
  })

  it('renders multiple selected files', () => {
    const files = [
      createDefaultFile('first.csv', 1024, 'text/csv'),
      createDefaultFile('second.csv.gz', 2048, 'application/gzip'),
    ]

    vi.mocked(useDropzone).mockReturnValue({
      getRootProps: vi.fn(() => ({})),
      getInputProps: vi.fn(() => ({})),
      isDragActive: false,
      isFocused: false,
      isDragAccept: false,
      isDragReject: false,
      isFileDialogActive: false,
      acceptedFiles: [],
      fileRejections: [],
      open: vi.fn(),
    } as unknown as ReturnType<typeof useDropzone>)

    render(
      <FileDropzone
        onFilesSelected={mockOnFilesSelected}
        onFileRemove={mockOnFileRemove}
        selectedFiles={files}
      />
    )

    expect(screen.getByText('first.csv')).toBeInTheDocument()
    expect(screen.getByText('second.csv.gz')).toBeInTheDocument()
  })

  it('renders delete button for each file', () => {
    const file = createDefaultFile('test.csv', 1024, 'text/csv')

    vi.mocked(useDropzone).mockReturnValue({
      getRootProps: vi.fn(() => ({})),
      getInputProps: vi.fn(() => ({})),
      isDragActive: false,
      isFocused: false,
      isDragAccept: false,
      isDragReject: false,
      isFileDialogActive: false,
      acceptedFiles: [],
      fileRejections: [],
      open: vi.fn(),
    } as unknown as ReturnType<typeof useDropzone>)

    render(
      <FileDropzone
        onFilesSelected={mockOnFilesSelected}
        onFileRemove={mockOnFileRemove}
        selectedFiles={[file]}
      />
    )

    const deleteButtons = screen.getAllByRole('button', { name: /remove file/i })
    expect(deleteButtons).toHaveLength(1)
  })

  it('calls onFileRemove when delete button is clicked', () => {
    const file = createDefaultFile('test.csv', 1024, 'text/csv')
    const mockRemove = vi.fn()

    vi.mocked(useDropzone).mockReturnValue({
      getRootProps: vi.fn(() => ({})),
      getInputProps: vi.fn(() => ({})),
      isDragActive: false,
      isFocused: false,
      isDragAccept: false,
      isDragReject: false,
      isFileDialogActive: false,
      acceptedFiles: [],
      fileRejections: [],
      open: vi.fn(),
    } as unknown as ReturnType<typeof useDropzone>)

    render(
      <FileDropzone
        onFilesSelected={mockOnFilesSelected}
        onFileRemove={mockRemove}
        selectedFiles={[file]}
      />
    )

    const deleteButton = screen.getByRole('button', { name: /remove file/i })
    fireEvent.click(deleteButton)

    expect(mockRemove).toHaveBeenCalledWith('test.csv')
  })

  it('shows drop files text when isDragActive is true', () => {
    vi.mocked(useDropzone).mockReturnValue({
      getRootProps: vi.fn(() => ({})),
      getInputProps: vi.fn(() => ({})),
      isDragActive: true,
      isFocused: false,
      isDragAccept: false,
      isDragReject: false,
      isFileDialogActive: false,
      acceptedFiles: [],
      fileRejections: [],
      open: vi.fn(),
    } as unknown as ReturnType<typeof useDropzone>)

    render(
      <FileDropzone
        onFilesSelected={mockOnFilesSelected}
        onFileRemove={mockOnFileRemove}
        selectedFiles={[]}
      />
    )

    expect(screen.getByText(/drop files here.../i)).toBeInTheDocument()
  })
})