'use client'

import { useState, useEffect } from 'react'
import { BookOpen, Brain, MessageCircle, Send, Loader2, Upload, File, Trash2 } from 'lucide-react'

interface SocraticResponse {
    clarifying_question: string
    concept_hint: string
    feedback: string
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

interface Subject {
    value: string
    label: string
}

interface Level {
    value: string
    label: string
}

interface Document {
    id: string
    filename: string
    subject: string
    level: string
    created_at: string
}

export default function Home() {
    const [selectedSubject, setSelectedSubject] = useState('physics')
    const [selectedLevel, setSelectedLevel] = useState('beginner')
    const [question, setQuestion] = useState('')
    const [response, setResponse] = useState<SocraticResponse | null>(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null)
    const [useRag, setUseRag] = useState(false)

    // State for document upload
    const [uploadFile, setUploadFile] = useState<File | null>(null)
    const [uploadSubject, setUploadSubject] = useState('general')
    const [uploadLevel, setUploadLevel] = useState('intermediate')
    const [uploadError, setUploadError] = useState('')
    const [uploadSuccess, setUploadSuccess] = useState('')
    const [showUploadForm, setShowUploadForm] = useState(false)

    // State for document list
    const [documents, setDocuments] = useState<Document[]>([])
    const [showDocuments, setShowDocuments] = useState(false)

    // State for available subjects and levels from the API
    const [availableSubjects, setAvailableSubjects] = useState<Subject[]>([
        { value: 'math', label: 'Math' },
        { value: 'physics', label: 'Physics' },
        { value: 'biology', label: 'Biology' },
        { value: 'history', label: 'History' },
        { value: 'chemistry', label: 'Chemistry' },
        { value: 'general', label: 'General' }
    ])

    const [availableLevels, setAvailableLevels] = useState<Level[]>([
        { value: 'beginner', label: 'Beginner' },
        { value: 'intermediate', label: 'Intermediate' },
        { value: 'advanced', label: 'Advanced' }
    ])

    // Fetch available subjects and levels on component mount
    useEffect(() => {
        const fetchOptions = async () => {
            try {
                const [subjectsRes, levelsRes] = await Promise.all([
                    fetch(`${API_URL}/subjects`),
                    fetch(`${API_URL}/levels`),
                ])

                if (subjectsRes.ok && levelsRes.ok) {
                    const subjects = await subjectsRes.json()
                    const levels = await levelsRes.json()

                    setAvailableSubjects(
                        subjects.subjects.map((s: string) => ({
                            value: s,
                            label: s.charAt(0).toUpperCase() + s.slice(1),
                        }))
                    )

                    setAvailableLevels(
                        levels.levels.map((l: string) => ({
                            value: l,
                            label: l.charAt(0).toUpperCase() + l.slice(1),
                        }))
                    )
                }
            } catch (err) {
                console.error('Failed to fetch options:', err)
            }
        }

        fetchOptions()
        fetchDocuments()
    }, [])

    // Function to fetch documents
    const fetchDocuments = async () => {
        try {
            const response = await fetch(`${API_URL}/documents`)
            if (response.ok) {
                const data = await response.json()
                setDocuments(data)
            } else {
                console.error('Failed to fetch documents')
            }
        } catch (err) {
            console.error('Error fetching documents:', err)
        }
    }

    // Function to handle file upload
    const handleUpload = async (e: React.FormEvent) => {
        e.preventDefault()

        if (!uploadFile) {
            setUploadError('Please select a file to upload')
            return
        }

        setUploadError('')
        setUploadSuccess('')

        // Create form data
        const formData = new FormData()
        formData.append('file', uploadFile)
        formData.append('subject', uploadSubject)
        formData.append('level', uploadLevel)

        try {
            const response = await fetch(`${API_URL}/documents/upload`, {
                method: 'POST',
                body: formData,
            })

            if (response.ok) {
                const data = await response.json()
                setUploadSuccess(`Document uploaded successfully: ${data.document.filename}`)
                setUploadFile(null)
                fetchDocuments() // Refresh document list
                setShowUploadForm(false) // Hide the form after successful upload
            } else {
                const errorData = await response.json()
                setUploadError(errorData.detail || 'Failed to upload document')
            }
        } catch (err) {
            setUploadError('Error uploading document')
            console.error('Upload error:', err)
        }
    }

    // Function to delete a document
    const handleDeleteDocument = async (id: string) => {
        try {
            const response = await fetch(`${API_URL}/documents/${id}`, {
                method: 'DELETE',
            })

            if (response.ok) {
                // Remove from state
                setDocuments(documents.filter(doc => doc.id !== id))
                // If this was the selected document, deselect it
                if (selectedDocumentId === id) {
                    setSelectedDocumentId(null)
                }
            } else {
                const errorData = await response.json()
                console.error('Failed to delete document:', errorData.detail)
            }
        } catch (err) {
            console.error('Error deleting document:', err)
        }
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        if (!question.trim()) {
            setError('Please enter a question')
            return
        }

        setError('')
        setLoading(true)

        try {
            // Determine which endpoint to use
            let endpoint = `${API_URL}/tutor`
            if (useRag) {
                endpoint = `${API_URL}/tutor/rag`
            }

            // Create request body
            const requestBody = {
                question,
                subject: selectedSubject,
                level: selectedLevel,
                document_id: selectedDocumentId
            }

            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody),
            })

            if (response.ok) {
                const data = await response.json()
                setResponse(data)
            } else {
                const errorData = await response.json()
                setError(errorData.detail || 'An error occurred while processing your question')
            }
        } catch (err) {
            setError('Failed to connect to the tutor service')
            console.error('Request error:', err)
        } finally {
            setLoading(false)
        }
    }

    // Get the selected document name for display
    const selectedDocumentName = selectedDocumentId
        ? documents.find(doc => doc.id === selectedDocumentId)?.filename || 'Selected document'
        : null

    return (
        <div className="min-h-screen bg-gray-900 text-white">
            <div className="container mx-auto px-4 py-8">
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center">
                        <Brain className="h-10 w-10 text-blue-500 mr-2" />
                        <h1 className="text-4xl font-bold">Socratic AI Tutor</h1>
                    </div>
                    <p className="mt-2 text-gray-400">
                        Ask questions and receive thoughtful guidance through Socratic questioning
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Left Column - Context */}
                    <div className="bg-gray-800 rounded-lg p-6 shadow-lg">
                        <div className="flex items-center mb-4">
                            <BookOpen className="h-6 w-6 text-blue-500 mr-2" />
                            <h2 className="text-xl font-semibold">Learning Context</h2>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1">
                                    Subject
                                </label>
                                <select
                                    value={selectedSubject}
                                    onChange={(e) => setSelectedSubject(e.target.value)}
                                    className="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                                >
                                    {availableSubjects.map((subject) => (
                                        <option key={subject.value} value={subject.value}>
                                            {subject.label}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1">
                                    Difficulty Level
                                </label>
                                <select
                                    value={selectedLevel}
                                    onChange={(e) => setSelectedLevel(e.target.value)}
                                    className="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                                >
                                    {availableLevels.map((level) => (
                                        <option key={level.value} value={level.value}>
                                            {level.label}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <div className="pt-4">
                                <div className="flex items-center justify-between mb-2">
                                    <label className="flex items-center text-sm font-medium text-gray-300 cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={useRag}
                                            onChange={(e) => setUseRag(e.target.checked)}
                                            className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 mr-2"
                                        />
                                        Use document knowledge
                                    </label>
                                    {documents.length > 0 && (
                                        <button
                                            type="button"
                                            onClick={() => setShowDocuments(!showDocuments)}
                                            className="text-xs text-blue-400 hover:text-blue-300"
                                        >
                                            {showDocuments ? 'Hide documents' : 'Show documents'}
                                        </button>
                                    )}
                                </div>

                                {useRag && (
                                    <div className="mt-2">
                                        {selectedDocumentName ? (
                                            <div className="flex items-center justify-between bg-gray-700 rounded-md p-2 text-sm">
                                                <span className="truncate">{selectedDocumentName}</span>
                                                <button
                                                    onClick={() => setSelectedDocumentId(null)}
                                                    className="text-gray-400 hover:text-gray-200"
                                                >
                                                    <Trash2 className="h-4 w-4" />
                                                </button>
                                            </div>
                                        ) : (
                                            <div className="text-gray-400 text-sm">
                                                No document selected
                                            </div>
                                        )}

                                        <div className="mt-2 flex space-x-2">
                                            <button
                                                type="button"
                                                onClick={() => setShowUploadForm(!showUploadForm)}
                                                className="text-xs px-2 py-1 bg-blue-600 hover:bg-blue-700 rounded text-white"
                                            >
                                                Upload Document
                                            </button>
                                            {documents.length > 0 && (
                                                <button
                                                    type="button"
                                                    onClick={() => setShowDocuments(!showDocuments)}
                                                    className="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded text-white"
                                                >
                                                    Select Document
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                )}

                                {showUploadForm && (
                                    <div className="mt-3 p-3 bg-gray-700 rounded-md">
                                        <h3 className="text-sm font-medium mb-2">Upload New Document</h3>
                                        <form onSubmit={handleUpload} className="space-y-3">
                                            <div>
                                                <label className="block text-xs text-gray-400 mb-1">
                                                    Select File
                                                </label>
                                                <input
                                                    type="file"
                                                    onChange={(e) => setUploadFile(e.target.files ? e.target.files[0] : null)}
                                                    className="block w-full text-sm text-gray-400
                                                    file:mr-4 file:py-1 file:px-2
                                                    file:rounded file:border-0
                                                    file:text-xs file:font-medium
                                                    file:bg-blue-500 file:text-white
                                                    hover:file:bg-blue-600"
                                                />
                                            </div>

                                            <div className="grid grid-cols-2 gap-2">
                                                <div>
                                                    <label className="block text-xs text-gray-400 mb-1">
                                                        Subject
                                                    </label>
                                                    <select
                                                        value={uploadSubject}
                                                        onChange={(e) => setUploadSubject(e.target.value)}
                                                        className="w-full bg-gray-600 border border-gray-500 rounded text-xs p-1"
                                                    >
                                                        {availableSubjects.map((subject) => (
                                                            <option key={subject.value} value={subject.value}>
                                                                {subject.label}
                                                            </option>
                                                        ))}
                                                    </select>
                                                </div>
                                                <div>
                                                    <label className="block text-xs text-gray-400 mb-1">
                                                        Level
                                                    </label>
                                                    <select
                                                        value={uploadLevel}
                                                        onChange={(e) => setUploadLevel(e.target.value)}
                                                        className="w-full bg-gray-600 border border-gray-500 rounded text-xs p-1"
                                                    >
                                                        {availableLevels.map((level) => (
                                                            <option key={level.value} value={level.value}>
                                                                {level.label}
                                                            </option>
                                                        ))}
                                                    </select>
                                                </div>
                                            </div>

                                            {uploadError && (
                                                <div className="text-red-400 text-xs">{uploadError}</div>
                                            )}
                                            {uploadSuccess && (
                                                <div className="text-green-400 text-xs">{uploadSuccess}</div>
                                            )}

                                            <div className="flex justify-end">
                                                <button
                                                    type="submit"
                                                    className="text-xs px-2 py-1 bg-blue-600 hover:bg-blue-700 rounded text-white"
                                                >
                                                    Upload
                                                </button>
                                                <button
                                                    type="button"
                                                    onClick={() => setShowUploadForm(false)}
                                                    className="text-xs px-2 py-1 bg-gray-600 hover:bg-gray-500 rounded text-white ml-2"
                                                >
                                                    Cancel
                                                </button>
                                            </div>
                                        </form>
                                    </div>
                                )}

                                {showDocuments && documents.length > 0 && (
                                    <div className="mt-3 p-3 bg-gray-700 rounded-md">
                                        <h3 className="text-sm font-medium mb-2">Your Documents</h3>
                                        <div className="max-h-40 overflow-y-auto">
                                            <ul className="space-y-1">
                                                {documents.map((doc) => (
                                                    <li key={doc.id} className="flex justify-between items-center text-sm">
                                                        <label className="flex items-center cursor-pointer">
                                                            <input
                                                                type="radio"
                                                                name="document"
                                                                checked={selectedDocumentId === doc.id}
                                                                onChange={() => setSelectedDocumentId(doc.id)}
                                                                className="h-3 w-3 text-blue-600 mr-2"
                                                            />
                                                            <span className="truncate">{doc.filename}</span>
                                                        </label>
                                                        <button
                                                            onClick={() => handleDeleteDocument(doc.id)}
                                                            className="text-gray-400 hover:text-red-400"
                                                        >
                                                            <Trash2 className="h-3 w-3" />
                                                        </button>
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Middle Column - Question */}
                    <div className="bg-gray-800 rounded-lg p-6 shadow-lg">
                        <div className="flex items-center mb-4">
                            <MessageCircle className="h-6 w-6 text-blue-500 mr-2" />
                            <h2 className="text-xl font-semibold">Your Question</h2>
                        </div>

                        <form onSubmit={handleSubmit}>
                            <textarea
                                value={question}
                                onChange={(e) => setQuestion(e.target.value)}
                                placeholder="Ask your question here... (e.g., 'Why is the sky blue?')"
                                className="w-full h-64 bg-gray-700 border border-gray-600 rounded-md py-3 px-4 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                            ></textarea>

                            {error && (
                                <div className="mt-3 bg-red-900/50 border border-red-800 p-3 rounded-md text-red-300 text-sm">
                                    {error}
                                </div>
                            )}

                            <button
                                type="submit"
                                disabled={loading || !question.trim()}
                                className="mt-4 w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:text-gray-400 text-white font-medium py-2 px-4 rounded-md transition-colors flex items-center justify-center"
                            >
                                {loading ? (
                                    <>
                                        <Loader2 className="animate-spin mr-2 h-5 w-5" />
                                        Getting guidance...
                                    </>
                                ) : (
                                    <>
                                        <Send className="mr-2 h-5 w-5" />
                                        Ask for Guidance
                                    </>
                                )}
                            </button>
                        </form>
                    </div>

                    {/* Right Column - Response */}
                    <div className="bg-gray-800 rounded-lg p-6 shadow-lg">
                        <div className="flex items-center mb-4">
                            <Brain className="h-6 w-6 text-blue-500 mr-2" />
                            <h2 className="text-xl font-semibold">AI Tutor Response</h2>
                        </div>

                        {response ? (
                            <div className="space-y-6">
                                <div>
                                    <h3 className="text-blue-400 font-medium mb-2">Clarifying Question</h3>
                                    <p className="bg-gray-700 p-3 rounded-md">{response.clarifying_question}</p>
                                </div>

                                <div>
                                    <h3 className="text-blue-400 font-medium mb-2">Concept Hint</h3>
                                    <p className="bg-gray-700 p-3 rounded-md">{response.concept_hint}</p>
                                </div>

                                <div>
                                    <h3 className="text-blue-400 font-medium mb-2">Feedback</h3>
                                    <p className="bg-gray-700 p-3 rounded-md">{response.feedback}</p>
                                </div>
                            </div>
                        ) : (
                            <div className="flex items-center justify-center h-64 text-gray-500">
                                <div className="text-center">
                                    <Brain className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                    <p>Ask a question to receive Socratic guidance</p>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
} 