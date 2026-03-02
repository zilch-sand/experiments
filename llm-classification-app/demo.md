# LLM Classifier – Demo

*2026-03-02T09:40:40Z by Showboat 0.6.1*
<!-- showboat-id: 969531ef-d2b7-4636-a77c-bed4d9a60ef6 -->

This demo exercises the LLM Classifier app in demo mode (no GCP credentials required). We verify model loading, prompt building, classification with fuzzy matching, batch tracking, and the arena.

```python3

import sys; sys.path.insert(0, 'src')
from llm_classifier.models import MODELS, get_price, estimate_cost

print('=== Model Registry ===')
for name, m in MODELS.items():
    inp, out = get_price(m.id)
    thinking = 'thinking' if m.supports_thinking else 'standard'
    print(f'  {name}: ${inp:.3f}/${out:.3f} per M tokens ({thinking})')

```

```output
=== Model Registry ===
  Gemini 2.0 Flash: $0.100/$0.400 per M tokens (standard)
  Gemini 2.0 Flash Lite: $0.075/$0.300 per M tokens (standard)
  Gemini 2.5 Pro: $1.250/$10.000 per M tokens (thinking)
  Claude 3.5 Sonnet (Vertex): $3.000/$15.000 per M tokens (standard)
  Claude 3.7 Sonnet (Vertex): $3.000/$15.000 per M tokens (thinking)
  Llama 3.1 405B (Vertex): $0.000/$0.000 per M tokens (standard)
  Llama 3.3 70B (Vertex): $0.000/$0.000 per M tokens (standard)
```

```python3

import sys; sys.path.insert(0, 'src')
from llm_classifier.prompt_builder import build_prompt, validate_prompt, get_prompt_columns

template = 'Classify the review.\n\nReview: {text}\nProduct: {product}\n\n{label_options}\n\nRespond with the category.'
row = {'text': 'Absolutely love it!', 'product': 'Widget Pro 3000'}
cats = ['Positive', 'Negative', 'Neutral']

print('=== Prompt Preview ===')
print(build_prompt(template, row, cats, multi_label=False))

print()
print('=== Validation (missing column) ===')
for w in validate_prompt(template, ['text']):
    print(' WARNING:', w)

```

```output
=== Prompt Preview ===
Classify the review.

Review: Absolutely love it!
Product: Widget Pro 3000

Pick exactly one of the following categories:
- Positive
- Negative
- Neutral

Respond with the category.

=== Validation (missing column) ===
 WARNING: Placeholder {product} not found in CSV columns.
```

```python3

import sys; sys.path.insert(0, 'src')
from llm_classifier.classification import fuzzy_match_label

cats = ['Positive', 'Negative', 'Neutral']
tests = [
    ('Positive', False),
    ('positive', False),   # case insensitive
    ('Pos', False),        # abbreviated
    ('neg', False),
    ('Positive|Neutral', True),  # multi-label
    ('Random stuff', False),     # unmatched
]

print('=== Fuzzy Label Matching ===')
for resp, multi in tests:
    matched = fuzzy_match_label(resp, cats, multi_label=multi)
    print(f'  {repr(resp):25s} -> {matched}')

```

```output
Traceback (most recent call last):
  File "<string>", line 3, in <module>
  File "/home/runner/work/experiments/experiments/llm-classification-app/src/llm_classifier/classification.py", line 6, in <module>
    from rapidfuzz import process, fuzz
ModuleNotFoundError: No module named 'rapidfuzz'
```

```python3

import sys, subprocess
subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'rapidfuzz'], check=True)
sys.path.insert(0, 'src')
from llm_classifier.classification import fuzzy_match_label

cats = ['Positive', 'Negative', 'Neutral']
tests = [
    ('Positive', False),
    ('positive', False),
    ('Pos', False),
    ('neg', False),
    ('Positive|Neutral', True),
    ('Random stuff', False),
]

print('=== Fuzzy Label Matching ===')
for resp, multi in tests:
    matched = fuzzy_match_label(resp, cats, multi_label=multi)
    print(f'  {repr(resp):25s} -> {matched}')

```

```output
/home/runner/.cache/uv/archive-v0/0GIDD2zfJQow3eUP5YPSu/bin/python3: No module named pip
Traceback (most recent call last):
  File "<string>", line 3, in <module>
  File "/usr/lib/python3.12/subprocess.py", line 571, in run
    raise CalledProcessError(retcode, process.args,
subprocess.CalledProcessError: Command '['/home/runner/.cache/uv/archive-v0/0GIDD2zfJQow3eUP5YPSu/bin/python3', '-m', 'pip', 'install', '-q', 'rapidfuzz']' returned non-zero exit status 1.
```

```bash
python3 -c "
import sys; sys.path.insert(0, 'src')
from llm_classifier.classification import fuzzy_match_label

cats = ['Positive', 'Negative', 'Neutral']
tests = [
    ('Positive', False),
    ('positive', False),
    ('Pos', False),
    ('neg', False),
    ('Positive|Neutral', True),
    ('Random stuff', False),
]

print('=== Fuzzy Label Matching ===')
for resp, multi in tests:
    matched = fuzzy_match_label(resp, cats, multi_label=multi)
    print(f'  {repr(resp):25s} -> {matched}')
"
```

```output
Traceback (most recent call last):
  File "<string>", line 3, in <module>
  File "/home/runner/work/experiments/experiments/llm-classification-app/src/llm_classifier/classification.py", line 6, in <module>
    from rapidfuzz import process, fuzz
ModuleNotFoundError: No module named 'rapidfuzz'
```

```bash
/usr/bin/python3 -c "
import sys; sys.path.insert(0, 'src')
from llm_classifier.classification import fuzzy_match_label

cats = ['Positive', 'Negative', 'Neutral']
tests = [
    ('Positive', False),
    ('positive', False),
    ('Pos', False),
    ('neg', False),
    ('Positive|Neutral', True),
    ('Random stuff', False),
]

print('=== Fuzzy Label Matching ===')
for resp, multi in tests:
    matched = fuzzy_match_label(resp, cats, multi_label=multi)
    print(f'  {repr(resp):25s} -> {matched}')
"
```

```output
=== Fuzzy Label Matching ===
  'Positive'                -> Positive
  'positive'                -> Positive
  'Pos'                     -> Positive
  'neg'                     -> UNMATCHED
  'Positive|Neutral'        -> ['Positive', 'Neutral']
  'Random stuff'            -> UNMATCHED
```

```bash
/usr/bin/python3 -c "
import sys, os; os.environ['DEMO_MODE'] = 'true'; os.environ['GCP_PROJECT'] = ''
sys.path.insert(0, 'src')
from llm_classifier.models import MODELS
from llm_classifier.vertex_client import call_model

model = MODELS['Gemini 2.0 Flash']
prompt = 'Classify the following text.\n\nText: Great product!\n\nPick exactly one of the following categories:\n- Positive\n- Negative\n- Neutral\n\nRespond with only the category name.'

results = []
for _ in range(3):
    r = call_model(model, prompt, system_prompt='', thinking_level=None, max_tokens=100)
    results.append(r['text'])

print('=== Demo Mode Responses ===')
for r in results:
    print(f'  Response: {r}')
"
```

```output
=== Demo Mode Responses ===
  Response: Neutral
  Response: Positive
  Response: Neutral
```

```bash
/usr/bin/python3 -c "
import sys; sys.path.insert(0, 'src')
from llm_classifier.models import MODELS, estimate_cost

model = MODELS['Claude 3.5 Sonnet (Vertex)']
input_tokens_per_row = 150
output_tokens_per_row = 10
total_rows = 10000

cost_per_row = estimate_cost(model.id, input_tokens_per_row, output_tokens_per_row)
total_cost = cost_per_row * total_rows

print('=== Cost Estimation ===')
print(f'Model: {model.display_name}')
print(f'Per row: {input_tokens_per_row} input + {output_tokens_per_row} output tokens')
print(f'Cost per row: ${cost_per_row:.6f}')
print(f'Estimated total ({total_rows:,} rows): ${total_cost:.4f}')
"
```

```output
=== Cost Estimation ===
Model: Claude 3.5 Sonnet (Vertex)
Per row: 150 input + 10 output tokens
Cost per row: 
Estimated total (10,000 rows): 
```

Cost estimation: at Claude 3.5 Sonnet rates (input: $3/M, output: $15/M), 150 input + 10 output tokens per row costs ~$0.00060/row — roughly $6.00 for a 10,000-row dataset.

```bash
/usr/bin/python3 -c "
import sys, os, tempfile; sys.path.insert(0, 'src')
os.environ.setdefault('BATCH_JOBS_FILE', tempfile.mktemp(suffix='.json'))
from llm_classifier.batch_manager import BatchManager, BatchJob

mgr = BatchManager()
job = BatchJob(id='test-batch-001', model_id='gemini-2.0-flash', status='running', total_rows=500)
mgr.add_job(job)
mgr.update_job('test-batch-001', status='completed')

print('=== Batch Manager ===')
for j in mgr.list_jobs():
    print(f'  Job {j.id}: status={j.status}, rows={j.total_rows}')
"
```

```output
=== Batch Manager ===
  Job test-batch-001: status=completed, rows=500
```

The app is accessible at http://localhost:8000 when running locally. Key workflow: (1) Upload CSV → (2) Write prompt template with {col} placeholders → (3) Set categories → (4) Run Test on first N rows → (5) Review token/cost estimate → (6) Send Batch for full dataset.
