import { Globe2 } from 'lucide-react';

import { useDashboard } from '../state/DashboardContext';
import { formatNumber } from '../utils/format';
import { StatusMessage } from './StatusMessage';

export function ExternalContext() {
  const { currencyContext, externalLoading, externalError } = useDashboard();

  if (externalLoading && !currencyContext) {
    return <StatusMessage state="loading" title="Loading currency context" />;
  }
  if (externalError) {
    return <StatusMessage state="error" title="Unable to load currency context" detail={externalError} />;
  }
  if (!currencyContext) {
    return <StatusMessage state="empty" title="No external context available" />;
  }

  return (
    <section className="external-panel" aria-label="External currency context">
      <div className="panel-heading">
        <div>
          <h2>Currency Context</h2>
          <span>REST Countries API status: {currencyContext.status}</span>
        </div>
        <Globe2 size={22} aria-hidden="true" />
      </div>
      <div className="external-summary">
        <strong>{currencyContext.currency}</strong>
        <span>{formatNumber(currencyContext.countries_using_currency)} countries using source currency</span>
      </div>
      {currencyContext.top_countries.length ? (
        <div className="country-grid">
          {currencyContext.top_countries.map((country) => (
            <article key={country.code}>
              <strong>{country.name}</strong>
              <span>{country.region}</span>
              <small>
                {formatNumber(country.population)} people
                {country.population_density ? `, ${country.population_density}/sq km` : ''}
              </small>
            </article>
          ))}
        </div>
      ) : (
        <StatusMessage
          state="empty"
          title="Country context is temporarily unavailable"
          detail="The dashboard is using local order data and will retry REST Countries on the next refresh."
        />
      )}
    </section>
  );
}
