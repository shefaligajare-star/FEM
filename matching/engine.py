import re
from typing import List, Dict, Any
from mentors.models import MentorProfile, MentorExperience, Expertise
from .models import Problem, MentorMatch

# Domain ontology mapping keywords to specific functional areas
DOMAIN_KEYWORDS = {
    'finance': ['cash', 'cashflow', 'cash-flow', 'capital', 'working capital', 'liquidity', 'loss', 'profit', 'margin', 'pricing', 'price', 'cost', 'debt', 'loan', 'accounting', 'budget', 'runway', 'funding', 'investor', 'equity'],
    'marketing': ['customer', 'customers', 'sales', 'lead', 'leads', 'traffic', 'visibility', 'marketing', 'branding', 'brand', 'advertising', 'social media', 'online', 'digital', 'acquisition', 'campaign', 'channel', 'seo'],
    'operations': ['supply', 'supply-chain', 'supply chain', 'inventory', 'logistics', 'vendor', 'supplier', 'manufacturing', 'production', 'quality', 'packaging', 'transport', 'spoilage', 'distribution'],
    'strategy': ['business plan', 'model', 'scaling', 'expansion', 'growth', 'competitor', 'pivot', 'market entry', 'regulations', 'license', 'partner'],
    'agriculture': ['farm', 'farmer', 'farming', 'agri', 'organic', 'crop', 'harvest', 'dairy', 'produce', 'rural', 'village', 'soil', 'irrigation', 'food processing'],
    'tech': ['website', 'app', 'software', 'e-commerce', 'ecommerce', 'digital', 'pos', 'tech', 'automation', 'platform'],
}

def tokenize(text: str) -> set:
    """Extract clean lowercase word tokens."""
    if not text:
        return set()
    words = re.findall(r'\b[a-z]{3,}\b', text.lower())
    stopwords = {'the', 'and', 'for', 'with', 'that', 'this', 'from', 'have', 'are', 'was', 'were', 'our', 'my', 'how', 'what', 'can', 'not', 'but', 'out'}
    return set(words) - stopwords

def calculate_match_breakdown(problem: Problem, mentor: MentorProfile) -> Dict[str, Any]:
    """
    Computes transparent multi-factor match scores between an Entrepreneur's Problem
    and a Mentor's profile & verified experience.
    Weights:
      Expertise Match: 30%
      Problem Similarity: 30%
      Industry Experience: 15%
      Business Stage: 10%
      Rural Experience: 10%
      Relevant Mentoring Outcomes: 5%
    """
    problem_text = f"{problem.title} {problem.description}".lower()
    prob_tokens = tokenize(problem_text)

    # 1. Expertise Match (30%)
    mentor_expertises = list(mentor.expertises.all())
    expertise_names = [exp.name.lower() for exp in mentor_expertises]
    
    # Check domain overlap
    matched_domains = []
    for domain, kws in DOMAIN_KEYWORDS.items():
        if any(kw in problem_text for kw in kws):
            matched_domains.append(domain)

    expertise_hits = 0
    for exp in expertise_names:
        for domain in matched_domains:
            if domain in exp or any(kw in exp for kw in DOMAIN_KEYWORDS.get(domain, [])):
                expertise_hits += 1
                break

    if matched_domains:
        expertise_score = min(98, max(55, int((expertise_hits / len(matched_domains)) * 75 + 25)))
    else:
        expertise_score = 75

    # 2. Problem Similarity (30%)
    experiences = list(mentor.experiences.all())
    best_sim = 50
    best_exp_match = None

    for exp in experiences:
        exp_text = f"{exp.problem_type} {exp.description} {exp.outcome}".lower()
        exp_tokens = tokenize(exp_text)
        overlap = prob_tokens.intersection(exp_tokens)
        sim = len(overlap) / (len(prob_tokens) or 1)
        sim_score = int(min(98, max(45, 50 + (sim * 150))))
        if sim_score > best_sim:
            best_sim = sim_score
            best_exp_match = exp

    problem_similarity_score = best_sim

    # 3. Industry Experience (15%)
    mentor_industry = (mentor.primary_industry or '').lower()
    prob_industry = (problem.industry or '').lower()
    prob_ind_tokens = tokenize(prob_industry)
    mentor_ind_tokens = tokenize(mentor_industry)
    
    if prob_industry and mentor_industry and (prob_industry in mentor_industry or mentor_industry in prob_industry):
        industry_score = 96
    elif len(prob_ind_tokens.intersection(mentor_ind_tokens)) > 0:
        industry_score = 90
    else:
        # Check if mentor had experience in this industry
        has_industry_exp = any(prob_industry in exp.industry.lower() for exp in experiences)
        industry_score = 88 if has_industry_exp else 68

    # 4. Business Stage (10%)
    preferred_stages = (mentor.preferred_stages or '').lower()
    prob_stage = (problem.business_stage or '').lower()
    if prob_stage in preferred_stages or not prob_stage:
        business_stage_score = 94
    else:
        business_stage_score = 72

    # 5. Rural Experience (10%)
    if problem.is_rural_business:
        if mentor.rural_business_experience:
            rural_experience_score = min(98, 85 + min(13, mentor.rural_businesses_count))
        else:
            rural_experience_score = 50
    else:
        rural_experience_score = 85

    # 6. Relevant Mentoring Outcomes (5%)
    try:
        credits = mentor.credits
        outcomes_score = min(98, 70 + min(28, credits.successful_outcomes))
    except Exception:
        outcomes_score = 75

    # Weighted Composite Match Score
    composite_score = int(
        (expertise_score * 0.30) +
        (problem_similarity_score * 0.30) +
        (industry_score * 0.15) +
        (business_stage_score * 0.10) +
        (rural_experience_score * 0.10) +
        (outcomes_score * 0.05)
    )

    # Ensure range 50 - 99 for realistic credibility
    composite_score = min(98, max(52, composite_score))

    # Construct Human-Centered Natural Explanation
    explanations = []
    if mentor_expertises:
        top_exp_names = ", ".join([e.name for e in mentor_expertises[:2]])
        explanations.append(f"Specializes deeply in {top_exp_names}")

    if best_exp_match:
        explanations.append(f"Has directly solved '{best_exp_match.problem_type}' challenges: \"{best_exp_match.outcome}\"")
    elif len(experiences) > 0:
        explanations.append(f"Has hands-on track record resolving {len(experiences)} verified operational and financial bottlenecks")

    if problem.is_rural_business and mentor.rural_business_experience:
        try:
            rb_count = mentor.credits.rural_businesses_supported
            explanations.append(f"Proven rural-business advisor with {rb_count} rural enterprises actively guided")
        except Exception:
            explanations.append("Extensive on-the-ground experience with regional & rural business environments")

    if business_stage_score >= 85:
        explanations.append(f"Actively mentors enterprises at your current growth phase ({problem.business_stage or 'Early Traction'})")

    try:
        if mentor.credits.successful_outcomes > 0:
            explanations.append(f"Maintains {mentor.credits.successful_outcomes} documented successful mentoring outcomes with a {mentor.credits.positive_feedback_rating}★ peer rating")
    except Exception:
        pass

    explanation_text = "\n".join(f"• {item}" for item in explanations)

    return {
        'match_score': composite_score,
        'expertise_score': expertise_score,
        'problem_similarity_score': problem_similarity_score,
        'industry_score': industry_score,
        'business_stage_score': business_stage_score,
        'rural_experience_score': rural_experience_score,
        'outcomes_score': outcomes_score,
        'explanation': explanation_text
    }

def run_matching_engine_for_problem(problem: Problem, top_n: int = 5) -> List[MentorMatch]:
    """
    Evaluates all active mentors against the problem, ranks them by composite match score,
    persists/updates MentorMatch records, and returns the top matches.
    """
    mentors = MentorProfile.objects.filter(is_accepting_mentees=True).select_related('user', 'credits').prefetch_related('expertises', 'experiences')
    
    matches = []
    for mentor in mentors:
        # Don't match entrepreneur with their own mentor profile if any
        if mentor.user == problem.entrepreneur:
            continue

        breakdown = calculate_match_breakdown(problem, mentor)
        
        match_obj, created = MentorMatch.objects.update_or_create(
            problem=problem,
            mentor=mentor,
            defaults=breakdown
        )
        matches.append(match_obj)

    matches.sort(key=lambda m: m.match_score, reverse=True)
    
    # Update problem status
    if matches and problem.status == Problem.STATUS_CHOICES[0][0]: # 'OPEN'
        problem.status = 'MATCHED'
        problem.save(update_fields=['status'])

    return matches[:top_n]
