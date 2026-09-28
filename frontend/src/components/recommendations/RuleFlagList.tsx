import type { RuleFlag } from '../../types/recommendations'
import { flagHeading } from '../../utils/recommendations'

type RuleFlagListProps = {
  flags: RuleFlag[]
}

export function RuleFlagList({ flags }: RuleFlagListProps) {
  if (flags.length === 0) return null

  return (
    <section className="flag-list" aria-label="Things to consider">
      <h3>Things to consider</h3>
      <ul>
        {flags.map((flag, index) => (
          <li key={`${flag.rule_code}-${flag.element_id ?? index}`}>
            <p className="flag-heading">{flagHeading(flag)}</p>
            <p>{flag.reason}</p>
          </li>
        ))}
      </ul>
    </section>
  )
}
