import axios from 'axios'

export interface CitationChunk {
	chunk_id: string
	title: string
	url: string
	score: number
	text: string
}

export async function retrieve(query: string, topK = 5): Promise<CitationChunk[]> {
	const r = await axios.post(process.env.NEXT_PUBLIC_SEARCH_ENDPOINT || 'http://localhost:8000/search', { query, top_k: topK })
	return r.data.results as CitationChunk[]
}

