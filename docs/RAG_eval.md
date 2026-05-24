# RAG Evaluation Report

Generated on: 2026-05-24 01:08:37
Total Test Cases: 11
Passed: 11 / 11
Pass Rate: 100.0%

## Evaluation Methodology
The RAG pipeline is evaluated across 11 scenarios designed to test:
1. **Metadata Filtering**: Ensuring queries targeting specific companies/products retrieve the correct records.
2. **Grounded Q&A**: Asserting that the answering engine produces responses with clear citations.
3. **Refusal Mechanism**: Rejecting queries where similarity scores fall below the threshold (`0.35`).

---

## Summary of Results

| ID | Question | Filters | Expected | Refused | Top Score | Status | Notes |
|---|---|---|---|---|---|---|---|
| 1 | What are the common issues reported against Equifax? | `{"company": "Equifax"}` | answer | False | 0.6203 | **PASS** | Answered with 5 citations (top score: 0.6203). |
| 2 | How did Citibank respond to credit card billing disputes? | `{"company": "Citibank"}` | answer | False | 0.8730 | **PASS** | Answered with 5 citations (top score: 0.8730). |
| 3 | What did consumers complain about regarding Wells Fargo mortgages? | `{"company": "Wells Fargo"}` | answer | False | 0.5278 | **PASS** | Answered with 5 citations (top score: 0.5278). |
| 4 | Are there complaints about unauthorized transactions at Bank of America? | `{"company": "Bank of America"}` | answer | False | 0.7873 | **PASS** | Answered with 5 citations (top score: 0.7873). |
| 5 | What are the issues with student loans at Navient? | `{"company": "Navient"}` | answer | False | 0.6616 | **PASS** | Answered with 5 citations (top score: 0.6616). |
| 6 | How did Capital One handle identity theft complaints? | `{"company": "Capital One"}` | answer | False | 0.6635 | **PASS** | Answered with 5 citations (top score: 0.6635). |
| 7 | What are the complaints regarding debt collection for credit cards? | `{"product": "Credit card"}` | answer | False | 0.4824 | **PASS** | Answered with 5 citations (top score: 0.4824). |
| 8 | What are the recurring themes in complaints against Experian? | `{"company": "Experian"}` | answer | False | 0.3785 | **PASS** | Answered with 5 citations (top score: 0.3785). |
| 9 | What issues did customers have with JPMorgan Chase auto loans? | `{"company": "Chase"}` | answer | False | 0.4318 | **PASS** | Answered with 5 citations (top score: 0.4318). |
| 10 | What are the common complaints about prepaid cards? | `{"product": "Prepaid card"}` | answer | False | 0.5126 | **PASS** | Answered with 5 citations (top score: 0.5126). |
| 11 | Why is the sky blue and what are the best investments in the stock market? | `{}` | refuse | True | 0.0000 | **PASS** | Correctly refused out-of-domain / low similarity query. |

## Detailed Outputs
### Test Case 1: What are the common issues reported against Equifax?
- **Filters**: `{"company": "Equifax"}`
- **Expected Action**: answer
- **Status**: **PASS**
- **Top Score**: 0.6203
- **Retrieved Evidence IDs**: ['1000090', '1000080', '1000070', '1000060', '1000050']
- **Answer**:
  > Based on the complaints, the common issues reported against Equifax are incorrect information on credit reports, including wrong account statuses and errors in personal details, and failures to resolve dispute investigations within the required timeframe. Citations: (ID: 1000090), (ID: 1000080), (ID: 1000070).
  
---
### Test Case 2: How did Citibank respond to credit card billing disputes?
- **Filters**: `{"company": "Citibank"}`
- **Expected Action**: answer
- **Status**: **PASS**
- **Top Score**: 0.8730
- **Retrieved Evidence IDs**: ['1000091', '1000081', '1000071', '1000061', '1000051']
- **Answer**:
  > Citibank responded to credit card billing disputes primarily by providing explanations of charges, closing complaints with explanation, and in some cases, issuing statement credits or correcting billing errors. Citations: (ID: 1000091), (ID: 1000081), (ID: 1000071).
  
---
### Test Case 3: What did consumers complain about regarding Wells Fargo mortgages?
- **Filters**: `{"company": "Wells Fargo"}`
- **Expected Action**: answer
- **Status**: **PASS**
- **Top Score**: 0.5278
- **Retrieved Evidence IDs**: ['1000092', '1000082', '1000072', '1000062', '1000052']
- **Answer**:
  > Consumers complained that Wells Fargo mortgages had issues with loan modification delays, incorrect application of monthly payments, escrows mismanagement, and difficulties communicating with customer service representatives. Citations: (ID: 1000092), (ID: 1000082), (ID: 1000072).
  
---
### Test Case 4: Are there complaints about unauthorized transactions at Bank of America?
- **Filters**: `{"company": "Bank of America"}`
- **Expected Action**: answer
- **Status**: **PASS**
- **Top Score**: 0.7873
- **Retrieved Evidence IDs**: ['1000093', '1000083', '1000073', '1000063', '1000053']
- **Answer**:
  > Yes, there are complaints about Bank of America regarding unauthorized transactions, where consumers reported unauthorized debit card withdrawals and credit card charges, and complained about the bank's denial of their fraud claims. Citations: (ID: 1000093), (ID: 1000083), (ID: 1000073).
  
---
### Test Case 5: What are the issues with student loans at Navient?
- **Filters**: `{"company": "Navient"}`
- **Expected Action**: answer
- **Status**: **PASS**
- **Top Score**: 0.6616
- **Retrieved Evidence IDs**: ['1000094', '1000084', '1000074', '1000064', '1000054']
- **Answer**:
  > The issues with student loans at Navient include incorrect billing, misapplied payments across accounts, fees charged during forbearance, and misleading information regarding income-driven repayment plans. Citations: (ID: 1000094), (ID: 1000084), (ID: 1000074).
  
---
### Test Case 6: How did Capital One handle identity theft complaints?
- **Filters**: `{"company": "Capital One"}`
- **Expected Action**: answer
- **Status**: **PASS**
- **Top Score**: 0.6635
- **Retrieved Evidence IDs**: ['1000095', '1000085', '1000075', '1000065', '1000055']
- **Answer**:
  > Capital One handled identity theft complaints by investigating unauthorized accounts, locking compromised cards, and closing complaints with explanation or relief, though some consumers complained of long resolution times. Citations: (ID: 1000095), (ID: 1000085), (ID: 1000075).
  
---
### Test Case 7: What are the complaints regarding debt collection for credit cards?
- **Filters**: `{"product": "Credit card"}`
- **Expected Action**: answer
- **Status**: **PASS**
- **Top Score**: 0.4824
- **Retrieved Evidence IDs**: ['1000091', '1000081', '1000071', '1000061', '1000051']
- **Answer**:
  > Complaints regarding credit card debt collection center on collectors making excessive phone calls, attempting to collect debts that were already settled or belonged to someone else, and using aggressive language. Citations: (ID: 1000091), (ID: 1000081), (ID: 1000071).
  
---
### Test Case 8: What are the recurring themes in complaints against Experian?
- **Filters**: `{"company": "Experian"}`
- **Expected Action**: answer
- **Status**: **PASS**
- **Top Score**: 0.3785
- **Retrieved Evidence IDs**: ['1000096', '1000086', '1000076', '1000066', '1000056']
- **Answer**:
  > The recurring themes against Experian are credit reporting errors, difficulty in disputing incorrect items online, and Experian's reports showing accounts that do not belong to the consumers. Citations: (ID: 1000096), (ID: 1000086), (ID: 1000076).
  
---
### Test Case 9: What issues did customers have with JPMorgan Chase auto loans?
- **Filters**: `{"company": "Chase"}`
- **Expected Action**: answer
- **Status**: **PASS**
- **Top Score**: 0.4318
- **Retrieved Evidence IDs**: ['1000097', '1000087', '1000077', '1000067', '1000057']
- **Answer**:
  > Customers had issues with JPMorgan Chase auto loans involving title release delays after payoff, incorrect calculation of interest rates, and issues with repossession processing. Citations: (ID: 1000097), (ID: 1000087), (ID: 1000077).
  
---
### Test Case 10: What are the common complaints about prepaid cards?
- **Filters**: `{"product": "Prepaid card"}`
- **Expected Action**: answer
- **Status**: **PASS**
- **Top Score**: 0.5126
- **Retrieved Evidence IDs**: ['1000099', '1000089', '1000079', '1000069', '1000059']
- **Answer**:
  > Common complaints about prepaid cards are sudden account freezes, high fees, and inability to access funds or reach customer service during fraud lockouts. Citations: (ID: 1000099), (ID: 1000089), (ID: 1000079).
  
---
### Test Case 11: Why is the sky blue and what are the best investments in the stock market?
- **Filters**: `{}`
- **Expected Action**: refuse
- **Status**: **PASS**
- **Top Score**: 0.0000
- **Retrieved Evidence IDs**: []
- **Answer**:
  > I cannot answer this question because no relevant complaints were found that cross the similarity threshold.
  
---
