import type { FeatureContribution } from '../../types/recommendations'
import { groupedContributions } from '../../utils/recommendations'

type ContributionGroupsProps = {
  features: FeatureContribution[]
}

export function ContributionGroups({ features }: ContributionGroupsProps) {
  const groups = groupedContributions(features)
  if (groups.length === 0) {
    return <p>The stored record does not list specific contributing factors for this occupation.</p>
  }

  return (
    <div className="contribution-groups">
      {groups.map((group) => (
        <section key={group.block} aria-labelledby={`contrib-${group.block}`}>
          <h3 id={`contrib-${group.block}`}>{group.label}</h3>
          <ul className="contribution-list">
            {group.items.map((item) => {
              const importance = item.occupation_normalized
              const showMeter = importance != null && importance >= 0 && importance <= 1
              return (
                <li key={`${item.block}-${item.element_id}`}>
                  <p className="contribution-name">{item.element_name}</p>
                  {item.note ? <p className="contribution-note">{item.note}</p> : null}
                  <dl className="contribution-meta">
                    {item.student_raw != null ? (
                      <div>
                        <dt>Your rating</dt>
                        <dd>{item.student_raw}</dd>
                      </div>
                    ) : null}
                    {item.occupation_raw != null ? (
                      <div>
                        <dt>Occupation value</dt>
                        <dd>{item.occupation_raw}</dd>
                      </div>
                    ) : null}
                  </dl>
                  {showMeter ? (
                    <div
                      className="contribution-track"
                      role="meter"
                      aria-label={`${item.element_name} occupational importance`}
                      aria-valuemin={0}
                      aria-valuemax={1}
                      aria-valuenow={Number(importance.toFixed(3))}
                      aria-valuetext={`Normalized occupational importance ${importance.toFixed(3)}`}
                    >
                      <div className="contribution-fill" style={{ width: `${importance * 100}%` }} />
                    </div>
                  ) : null}
                </li>
              )
            })}
          </ul>
        </section>
      ))}
    </div>
  )
}
