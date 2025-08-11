import { retrieve } from './rag'
import OpenAI from 'openai'

const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY })

export async function answerWithRag(user: string){
	const citations = await retrieve(user, 5)
	const system = 'Responda em português. Inclua citações no formato [C1], [C2]...'
	const messages = [
		{ role: 'system', content: system },
		{ role: 'user', content: user + '\nContexto:\n' + citations.map((c,i)=>`[C${i+1}] ${c.text}`).join('\n') }
	] as any
	const resp = await client.chat.completions.create({
		model: process.env.OPENAI_MODEL || 'gpt-4o-mini',
		messages
	})
	return { text: resp.choices[0].message?.content || '', citations }
}

