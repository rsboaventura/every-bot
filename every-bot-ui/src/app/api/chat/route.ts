import { NextRequest } from 'next/server'
import { answerWithRag } from '../../../lib/agents'

export async function POST(req: NextRequest){
	const { message } = await req.json()
	const { text, citations } = await answerWithRag(message)
	return new Response(JSON.stringify({ reply: text, citations }), { headers: { 'Content-Type':'application/json' }})
}

