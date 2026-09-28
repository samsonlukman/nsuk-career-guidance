import type { ButtonHTMLAttributes } from 'react'
import { Link, type LinkProps } from 'react-router-dom'

type Variant = 'primary' | 'secondary' | 'ghost'

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant
}

function classNameFor(variant: Variant, extra?: string): string {
  return ['btn', `btn-${variant}`, extra].filter(Boolean).join(' ')
}

export function Button({ variant = 'primary', className, type = 'button', ...props }: ButtonProps) {
  return <button type={type} className={classNameFor(variant, className)} {...props} />
}

type ButtonLinkProps = LinkProps & {
  variant?: Variant
}

export function ButtonLink({ variant = 'primary', className, ...props }: ButtonLinkProps) {
  return <Link className={classNameFor(variant, className)} {...props} />
}
