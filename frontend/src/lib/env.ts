import { z } from 'zod'

const invalidUrlMessage =
  'must be an absolute HTTP(S) URL without credentials, query, or fragment'

const publicEnvSchema = z
  .object({
    VITE_API_URL: z.string().optional()
  })
  .superRefine(({ VITE_API_URL }, context) => {
    if (VITE_API_URL === undefined || VITE_API_URL === '') return

    let url: URL
    try {
      url = new URL(VITE_API_URL)
    } catch {
      context.addIssue({
        code: 'custom',
        path: ['VITE_API_URL'],
        message: invalidUrlMessage
      })
      return
    }

    const hasAbsoluteHttpUrlForm =
      /^https?:\/\/[^/?#\\\s@]+(?:\/[^?#\\\s]*)?$/i.test(VITE_API_URL)
    const usesHttpProtocol =
      url.protocol === 'http:' || url.protocol === 'https:'
    const hasNoCredentials = url.username === '' && url.password === ''

    if (
      !hasAbsoluteHttpUrlForm ||
      !usesHttpProtocol ||
      url.hostname === '' ||
      !hasNoCredentials
    ) {
      context.addIssue({
        code: 'custom',
        path: ['VITE_API_URL'],
        message: invalidUrlMessage
      })
    }
  })

type PublicEnv = Readonly<{ VITE_API_URL: string }>

export const parsePublicEnv = (environment: {
  readonly VITE_API_URL?: string
}): PublicEnv => {
  const result = publicEnvSchema.safeParse(environment)
  if (!result.success) {
    throw new Error(`Invalid VITE_API_URL: ${invalidUrlMessage}.`)
  }

  return { VITE_API_URL: result.data.VITE_API_URL ?? '' }
}
