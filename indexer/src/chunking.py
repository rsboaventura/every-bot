from typing import List, Iterator

def split_text(text:str, size:int, overlap:int) -> List[str]:
	chunks: List[str] = []
	start=0; n=len(text)
	while start < n:
		end = min(n, start+size)
		chunks.append(text[start:end])
		start = end - overlap
		if start < 0: start = 0
	return [c.strip() for c in chunks if c.strip()]

def iter_split(text:str, size:int, overlap:int) -> Iterator[str]:
	"""Generator version to reduce peak memory when streaming."""
	start=0; n=len(text)
	while start < n:
		end = min(n, start+size)
		chunk = text[start:end].strip()
		if chunk:
			yield chunk
		start = end - overlap
		if start < 0: start = 0
