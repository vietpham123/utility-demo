# Sample Data Models

## Customer
- Id (int)
- Name (string)
- Address (string)
- Email (string)
- Phone (string)

## Invoice
- Id (int)
- CustomerId (int)
- Amount (decimal)
- DueDate (date)
- Status (string)

## Payment
- Id (int)
- InvoiceId (int)
- Amount (decimal)
- Date (date)
- Method (string)
