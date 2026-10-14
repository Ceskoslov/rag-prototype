import { expect, test } from '@playwright/test'

// Browser contract fixtures; backend ingestion/stream persistence is tested separately.
test('chat citations, new sessions and document lifecycle', async ({ page }) => {
  const sessionIds: string[] = []
  let uploaded = false
  const source = { citation_id: 1, title: 'refund.md', source_path: 'refund.md', knowledge_base: 'policies', snippet: 'Refunds within 30 days.', content: 'Refunds within 30 days.\nComplete original evidence.', page: null }
  await page.route('**/api/v1/**', async route => {
    const request = route.request()
    const path = new URL(request.url()).pathname
    if (path.endsWith('/chat/stream')) {
      sessionIds.push(request.postDataJSON().session_id)
      const events = [{ type: 'progress', data: { stage: 'generate' } }, { type: 'token', content: 'Refunds within 30 days [1].' }, { type: 'sources', data: [source] }, { type: 'done', data: { grounded: true } }]
      await route.fulfill({ contentType: 'text/event-stream', body: events.map(event => `data: ${JSON.stringify(event)}\n\n`).join('') })
    } else if (path.endsWith('/sessions')) await route.fulfill({ json: [] })
    else if (path.endsWith('/knowledge-bases')) await route.fulfill({ json: [{ name: 'policies' }] })
    else if (path.endsWith('/documents')) await route.fulfill({ json: uploaded ? [{ source_path: 'uploaded.md', size: 30, indexed: true }] : [] })
    else if (path.includes('/jobs/')) await route.fulfill({ json: { status: 'complete', result: { status: 'success' } } })
    else if (request.method() === 'PUT') { uploaded = true; await route.fulfill({ status: 202, json: { job_id: 'upload-1' } }) }
    else if (request.method() === 'DELETE') { uploaded = false; await route.fulfill({ status: 202, json: { job_id: 'delete-1' } }) }
    else await route.fulfill({ status: 404, json: { detail: 'Missing fixture' } })
  })
  await page.goto('/')
  await page.getByLabel('Knowledge base', { exact: true }).selectOption('policies')
  await page.getByRole('textbox').fill('Refund window?')
  await page.getByRole('button', { name: 'Send' }).click()
  await expect(page.getByText('Answer passed the evidence check')).toBeVisible()
  await page.getByRole('button', { name: '1', exact: true }).click()
  await expect(page.getByLabel('Source evidence')).toContainText('Complete original evidence')
  await page.getByRole('button', { name: 'New chat', exact: true }).click()
  await page.getByRole('textbox').fill('Refund window again?')
  await page.getByRole('button', { name: 'Send' }).click()
  await expect(page.getByText('Answer passed the evidence check')).toBeVisible()
  expect(sessionIds[0]).not.toBe(sessionIds[1])
  await page.getByRole('button', { name: 'Documents', exact: true }).click()
  await page.getByLabel('Document', { exact: true }).setInputFiles({ name: 'uploaded.md', mimeType: 'text/markdown', buffer: Buffer.from('New document content') })
  await page.getByRole('button', { name: 'Upload and index' }).click()
  await expect(page.getByRole('status')).toContainText('complete')
  await expect(page.getByRole('cell', { name: 'uploaded.md' })).toBeVisible()
  await page.getByRole('button', { name: 'Delete and re-index' }).click()
  await expect(page.getByRole('cell', { name: 'uploaded.md' })).toHaveCount(0)
})

test('premature stream failure releases controls', async ({ page }) => {
  await page.route('**/api/v1/**', async route => {
    if (route.request().url().endsWith('/chat/stream')) await route.fulfill({ contentType: 'text/event-stream', body: 'data: {"type":"token","content":"Incomplete draft"}\n\n' })
    else await route.fulfill({ json: [] })
  })
  await page.goto('/')
  await page.getByRole('textbox').fill('Question')
  await page.getByRole('button', { name: 'Send' }).click()
  await expect(page.getByRole('alert')).toContainText('Connection ended')
  await expect(page.getByRole('textbox')).toBeEnabled()
})
