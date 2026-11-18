# NuvHome per Home Assistant

Porta in Home Assistant le bollette e le scadenze delle tue case di NuvHome. Solo lettura: la chiave non può cambiare né cancellare nulla.

## Cosa trovi

Per ogni casa un dispositivo con:

- **Luce, gas, acqua**: ultima bolletta (importo, periodo, fornitore), consumo, prezzo medio per unità, spesa degli ultimi 12 mesi
- **Scadenze**: prossima scadenza, quante ne hai nei prossimi 30 giorni, quante sono già superate
- **Bollette in scadenza**: quante e per quanto
- **Calendario «Scadenze»** con tasse, bollette, condominio, mutuo, assicurazione, manutenzione e promemoria

Home Assistant chiede i dati a NuvHome ogni 30 minuti: non serve aprire porte sulla tua rete.

## Installazione

1. Su NuvHome: Profilo, Privacy e dati, **Crea chiave per Home Assistant**. Copia la chiave (si vede una sola volta).
2. In Home Assistant, HACS, menu in alto a destra, **Repository personalizzati**: aggiungi l'indirizzo di questo repository come categoria **Integrazione**, poi scarica NuvHome e riavvia.
3. Impostazioni, Dispositivi e servizi, **Aggiungi integrazione**, cerca NuvHome e incolla la chiave.

Se revochi la chiave su NuvHome, Home Assistant ti chiede di incollarne una nuova.

## Esempio: avviso sul telefono

```yaml
automation:
  - alias: "Scadenza in arrivo"
    trigger:
      - platform: calendar
        event: start
        entity_id: calendar.casa_scadenze
        offset: "-3 days"
    action:
      - service: notify.mobile_app_il_mio_telefono
        data:
          message: "{{ trigger.calendar_event.summary }}"
```

## Cartella

Il componente sta in `custom_components/nuvhome/`. Il servizio che risponde sta in NuvHome (`/api/integrations/home-assistant/summary`).
