import { describe, expect, it } from 'vitest'
import { createClient } from '../client/client'
import { parsePublicEnv } from './env'

const apiPath = '/api/v1/users/me'

const requestUrl = (VITE_API_URL?: string) => {
  const environment = parsePublicEnv({ VITE_API_URL })
  const client = createClient({ baseURL: environment.VITE_API_URL })
  return client.buildUrl({ url: apiPath })
}

describe('public environment', () => {
  it.each([undefined, ''])('keeps %s API URL requests same-origin', value => {
    expect(parsePublicEnv({ VITE_API_URL: value }).VITE_API_URL).toBe('')
    expect(requestUrl(value)).toBe(apiPath)
  })

  it.each([
    'http://localhost:8000',
    'https://api.example.com',
    'https://api.example.com/service/v2',
    'https://api.example.com/service/',
    'http://[::1]:8000'
  ])('preserves the configured base URL %s', value => {
    expect(parsePublicEnv({ VITE_API_URL: value }).VITE_API_URL).toBe(value)
    expect(requestUrl(value)).toBe(`${value}${apiPath}`)
  })

  it.each([
    'not-a-url',
    '/api',
    '//api.example.com',
    'https:api.example.com',
    'https:///api.example.com',
    'https://',
    'https://api.example.com:invalid',
    'ftp://api.example.com',
    'javascript:alert(1)',
    'file:///api',
    'https://secret-user:secret-password@api.example.com',
    'https://secret-user@api.example.com',
    'https://@api.example.com',
    'https://api.example.com?token=secret-query',
    'https://api.example.com?',
    'https://api.example.com#secret-fragment',
    'https://api.example.com#',
    ' https://api.example.com',
    'https://api.example.com\n',
    'https://api.example.com\\private'
  ])('rejects invalid API URLs without disclosing them: %s', value => {
    let error: unknown
    try {
      requestUrl(value)
    } catch (caught) {
      error = caught
    }
    expect(error).toBeInstanceOf(Error)
    expect(String(error)).toContain('VITE_API_URL')
    expect(String(error)).not.toContain(value)
    expect(String(error)).not.toContain('secret-')
  })

  it('returns only the declared public setting', () => {
    const environment = {
      VITE_API_URL: 'https://api.example.com',
      DATABASE_PASSWORD: 'private-database-secret',
      MAILPIT_HOST: 'http://private-mailpit'
    }
    expect(parsePublicEnv(environment)).toEqual({
      VITE_API_URL: environment.VITE_API_URL
    })
    expect(parsePublicEnv({})).toEqual({ VITE_API_URL: '' })
  })
})
