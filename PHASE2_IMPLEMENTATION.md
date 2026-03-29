# Phase 2 Implementation Guide

## Overview

Phase 2 adds the following systems to the BEST Galaxy Assessment:

1. **AI Report Generation** - OpenAI-powered interpretation
2. **Payment Integration** - Stripe checkout for report unlocking
3. **Feature Gating** - Dynamic unlock mechanism
4. **Full Report Display** - Complete assessment results

## What's New in Phase 2

### Backend

#### 1. AI Service (`scoring_engine/ai_service.py`)
- OpenAI GPT-4o-mini integration for narrative generation
- Fallback to template-based interpretation if API unavailable
- Generates 6 report sections:
  - Executive Summary
  - Archetype Profile
  - PEI × BHP Interpretation
  - Strengths Analysis
  - Growth Edges Analysis
  - AIMS Plan

#### 2. Payment Service (`scoring_engine/payment_service.py`)
- Stripe checkout session creation
- Webhook signature verification
- Payment processing
- Report unlock mechanism
- Payment status tracking

#### 3. Updated API Endpoints
- `POST /api/v1/payment/create-checkout` - Create Stripe checkout session
- `POST /api/v1/payment/webhook` - Handle Stripe webhooks
- `GET /api/v1/payment/status/{assessment_id}` - Get payment status

#### 4. Database Schema Updates
- `payment_status` - 'free' or 'paid'
- `payment_id` - Stripe payment intent ID
- `upgraded_at` - Timestamp of upgrade

### Frontend

#### 1. FullReport Component
- Tabbed interface (Overview, Domains, Interpretation, AIMS)
- Complete assessment visualization
- AI-generated narratives display

#### 2. Updated LockedSections Component
- Payment flow integration
- Stripe checkout redirect
- Loading and error states

#### 3. PaymentSuccess Component
- Post-payment redirect handler
- Automatic full report loading
- Error handling

## Setup Instructions

### 1. Install Dependencies

```bash
pip3 install openai stripe --break-system-packages
```

### 2. Configure Environment Variables

Create/update `.env` file:

```bash
# Supabase (already configured)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key

# OpenAI API (Phase 2)
OPENAI_API_KEY=sk-proj-...

# Stripe API (Phase 2)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID=price_...
```

### 3. Update Supabase Schema

Run the updated migration in Supabase SQL Editor:

```sql
-- Add payment tracking columns
ALTER TABLE assessment_results 
ADD COLUMN IF NOT EXISTS payment_status TEXT NOT NULL DEFAULT 'free',
ADD COLUMN IF NOT EXISTS payment_id TEXT,
ADD COLUMN IF NOT EXISTS upgraded_at TIMESTAMPTZ;

-- Add index for payment status
CREATE INDEX IF NOT EXISTS idx_assessment_results_payment_status
    ON assessment_results (payment_status);
```

### 4. Configure Stripe

1. Create a Stripe account at https://stripe.com
2. Create a Product and Price in Stripe Dashboard
3. Copy the Price ID to `STRIPE_PRICE_ID` in `.env`
4. Set up webhook endpoint: `https://your-domain.com/api/v1/payment/webhook`
5. Copy webhook secret to `STRIPE_WEBHOOK_SECRET` in `.env`

## Usage

### Free Tier (ScoreCard)

```python
# API Request
POST /api/v1/assess
{
  "user_id": "user123",
  "report_type": "STUDENT_SUCCESS",
  "responses": [...],
  "tier": "free",
  "use_ai": false  # Use template-based interpretation
}

# Response: ScoreCard output
{
  "tier": "free",
  "galaxy_snapshot": {...},
  "constellation": [...],
  "lens_teasers": {...},
  "locked_features": [...]
}
```

### Paid Tier (Full Report)

```python
# API Request
POST /api/v1/assess
{
  "user_id": "user123",
  "report_type": "STUDENT_SUCCESS",
  "responses": [...],
  "tier": "paid",
  "use_ai": true  # Use OpenAI for interpretation
}

# Response: Full output with AI narratives
{
  "metadata": {...},
  "construct_scores": {...},
  "load_framework": {...},
  "domains": [...],
  "archetype": {...},
  "interpretation": {
    "executive_summary": "AI-generated summary...",
    "archetype_profile": "AI-generated profile...",
    ...
  }
}
```

### Payment Flow

1. User completes free assessment → gets ScoreCard
2. User clicks "Unlock Full Galaxy Report"
3. Frontend calls `/api/v1/payment/create-checkout`
4. User redirected to Stripe checkout
5. After payment, Stripe webhook fires
6. Backend unlocks report (`payment_status = 'paid'`)
7. User redirected to `/success?assessment_id=...`
8. Full report displayed

## Testing

### Test AI Generation (without OpenAI key)

```python
# Falls back to template-based interpretation
python3 -c "
from scoring_engine.ai_service import generate_ai_narrative
result = generate_ai_narrative('executive_summary', {}, 'STUDENT_SUCCESS')
print('AI available:', result is not None)
"
```

### Test Payment Flow (without Stripe key)

```bash
# Returns mock session
curl -X POST "http://localhost:8000/api/v1/payment/create-checkout?assessment_id=test-123&customer_email=test@example.com"
```

### Run All Tests

```bash
python3 -m pytest tests/ -v
```

## Cost Estimates

### OpenAI API
- Model: GPT-4o-mini
- Cost: ~$0.03 per full report
- 1,000 reports = $30/month
- 10,000 reports = $300/month

### Stripe
- 2.9% + $0.30 per transaction
- $29.99 report = $1.17 fee
- Net revenue = $28.82 per report

### Supabase
- Free tier: 500MB storage, 2GB bandwidth
- Pro tier ($25/mo): 8GB storage, 50GB bandwidth
- Scales to ~50,000 assessments on Pro tier

## Architecture Decisions

### Why Template Fallback?
- Ensures system works without OpenAI API key
- Zero cost for development/testing
- Graceful degradation if API fails

### Why Separate Payment Service?
- Decouples payment logic from scoring engine
- Easy to swap Stripe for other providers
- Testable without real payment processing

### Why Store Full Output for Free Users?
- Research data collection (Dr. Crump's requirement)
- Enables demographic analysis
- Allows retroactive unlocking after payment

## Troubleshooting

### "OpenAI API key not set"
- This is a warning, not an error
- System falls back to template-based interpretation
- Add `OPENAI_API_KEY` to `.env` to enable AI

### "Stripe not configured"
- Payment endpoints return mock responses
- Add Stripe keys to `.env` to enable real payments
- Use Stripe test mode for development

### "Failed to unlock report"
- Check Supabase connection
- Verify assessment_id exists in database
- Check payment_status column exists (run migration)

## Next Steps (Phase 3)

1. Email delivery system (SendGrid/Resend)
2. PDF report generation
3. User dashboard (view all assessments)
4. Admin analytics dashboard
5. A/B testing for conversion optimization
6. Multi-language support
7. White-label customization

## Support

For issues or questions:
1. Check logs: Backend shows detailed error messages
2. Verify environment variables are set correctly
3. Test with mock data first (no API keys needed)
4. Review Supabase logs for database errors
