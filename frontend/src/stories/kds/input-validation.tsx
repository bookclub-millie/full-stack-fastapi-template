import { Button } from '@kds/ui/components/button'
import { Field, FieldLabel } from '@kds/ui/components/field'
import { Input } from '@kds/ui/components/input'
import { useState } from 'react'
import { Specimen } from './specimen'

export const InputValidationExample = () => {
  const [name, setName] = useState('')
  const [error, setError] = useState(false)
  const [savedName, setSavedName] = useState('')

  return (
    <Specimen
      name="input-validation"
      title="Profile form"
      description="Required input validation and successful submission feedback."
    >
      <form
        noValidate
        className="grid gap-4"
        onSubmit={event => {
          event.preventDefault()
          const value = name.trim()
          setError(!value)
          setSavedName(value)
        }}
      >
        <Field>
          <FieldLabel htmlFor="profile-display-name">Display name</FieldLabel>
          <Input
            id="profile-display-name"
            required
            value={name}
            onChange={event => setName(event.target.value)}
            aria-invalid={error}
            aria-describedby={error ? 'profile-error' : undefined}
          />
          {error && (
            <p id="profile-error" role="alert">
              Enter a display name.
            </p>
          )}
        </Field>
        <Button type="submit">Save profile</Button>
        {savedName && <p role="status">Profile saved for {savedName}.</p>}
      </form>
    </Specimen>
  )
}
