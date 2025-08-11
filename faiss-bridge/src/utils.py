import logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger('faiss-bridge')

from numpy.typing import NDArray  # type: ignore[import-not-found]
import numpy as np  # type: ignore[import-not-found]

def cosine(a:NDArray, b:NDArray) -> float:  # type: ignore[type-arg]
	a32 = a.astype('float32', copy=False)
	b32 = b.astype('float32', copy=False)
	return float((a32 @ b32) / (( (a32*a32).sum()**0.5) * ((b32*b32).sum()**0.5) + 1e-9))

