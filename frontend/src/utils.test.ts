import { AxiosError, AxiosHeaders } from 'axios'
import { describe, expect, it, vi } from 'vitest'
import { getInitials, handleError } from './utils'

const apiError = (data: unknown, status = 422) => {
  const config = { headers: new AxiosHeaders() }
  return new AxiosError(
    'Request failed',
    'ERR_BAD_REQUEST',
    config,
    undefined,
    {
      config,
      data,
      status,
      statusText: 'Unprocessable Entity',
      headers: new AxiosHeaders()
    }
  )
}

describe('handleError', () => {
  it('presents the first FastAPI validation detail through the bound toast callback', () => {
    const firstMessage = 'The supplied email is invalid'
    const showErrorToast = vi.fn()
    const onError = handleError.bind(showErrorToast)

    onError(
      apiError({
        detail: [
          { loc: ['body', 'email'], msg: firstMessage, type: 'value_error' },
          { loc: ['body', 'password'], msg: 'Password too short' }
        ]
      })
    )

    expect(showErrorToast).toHaveBeenCalledExactlyOnceWith(firstMessage)
  })

  it('uses a FastAPI string detail instead of the generic HTTP error message', () => {
    const detail = 'An account with this email already exists'
    const showErrorToast = vi.fn()
    handleError.call(showErrorToast, apiError({ detail }, 400))
    expect(showErrorToast).toHaveBeenCalledExactlyOnceWith(detail)
  })

  it.each([{ detail: [] }, { detail: null }, { other: 'not an API detail' }])(
    'falls back to the Axios message when the response has no usable detail: %j',
    data => {
      const error = apiError(data)
      const showErrorToast = vi.fn()
      handleError.call(showErrorToast, error)
      expect(showErrorToast).toHaveBeenCalledExactlyOnceWith(error.message)
    }
  )

  it('presents network failures that have no HTTP response', () => {
    const error = new AxiosError('Network Error', 'ERR_NETWORK')
    const showErrorToast = vi.fn()
    handleError.call(showErrorToast, error)
    expect(showErrorToast).toHaveBeenCalledExactlyOnceWith(error.message)
  })

  it('does not expose internal error messages for non-HTTP errors', () => {
    const error = new Error('private internal exception context')
    const showErrorToast = vi.fn()
    handleError.call(showErrorToast, error)
    expect(showErrorToast).toHaveBeenCalledOnce()
    const [message] = showErrorToast.mock.calls[0]
    expect(message).toEqual(expect.any(String))
    expect(message.length).toBeGreaterThan(0)
    expect(message).not.toContain(error.message)
  })
})

describe('getInitials', () => {
  it.each([
    ['Ada Lovelace', 'AL'],
    ['grace brewster hopper', 'GB'],
    ['admin', 'A'],
    ['', '']
  ])('uses at most the first two words of %s', (name, initials) => {
    expect(getInitials(name)).toBe(initials)
  })
})
