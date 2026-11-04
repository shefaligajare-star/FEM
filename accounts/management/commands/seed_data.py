import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import User
from entrepreneurs.models import EntrepreneurProfile
from mentors.models import MentorProfile, MentorExperience, MentorCredit, AvailabilitySlot, Expertise
from matching.models import ProblemCategory, Problem, MentorMatch, MentoringRequest, MentoringSession
from matching.engine import run_matching_engine_for_problem
from community.models import CommunityPost, Comment, Reaction
from collaboration.models import CollaborationRequest, CollaborationInterest
from stories.models import Story
from messaging.models import Conversation, Message
from notifications.models import Notification

class Command(BaseCommand):
    help = "Populates FEM platform with rich, realistic, professional demo ecosystem data"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding FEM Platform with realistic startup & mentorship data..."))

        # 1. Expertises
        expertises_data = [
            ("Finance & Cash Flow", "finance-cash-flow", "Working capital management, unit economics, liquidity planning, debt structuring, and pricing models."),
            ("Business Planning & Strategy", "business-planning", "Strategic roadmaps, milestone planning, feasibility audits, and commercial execution."),
            ("Marketing & Customer Acquisition", "marketing-acquisition", "Offline distribution, regional retail entry, B2B sales pipelines, and digital visibility."),
            ("Supply Chain & Operations", "supply-chain-ops", "Procurement, vendor reliability, cold chain, packaging preservation, and logistics routing."),
            ("Food Processing & Manufacturing", "food-processing", "Quality standards, batch scaling, shelf-life stabilization, and regulatory compliance."),
            ("Rural Enterprise & Agritech", "rural-enterprise", "Farmer cooperatives, village-level aggregation, localized value addition, and rural market dynamics."),
            ("Branding & Packaging", "branding-packaging", "Premium positioning for regional crafts & agri-produce, eco-packaging, and consumer trust."),
            ("E-Commerce & Digital Presence", "ecommerce-digital", "Direct-to-consumer websites, regional logistics partnerships, and mobile payments."),
            ("Fundraising & Grants", "fundraising-grants", "Impact investment, angel syndicates, bank credit lines, and regional development grants."),
        ]

        expertise_objs = {}
        for name, slug, desc in expertises_data:
            obj, _ = Expertise.objects.get_or_create(slug=slug, defaults={'name': name, 'description': desc})
            expertise_objs[slug] = obj

        # 2. Problem Categories
        categories_data = [
            ("Cash Flow & Working Capital", "cash-flow", "Cash deficits, payment delays from distributors, and seasonal inventory lockup."),
            ("Pricing & Profit Margins", "pricing-margins", "Difficulty setting sustainable margins while remaining competitive in regional markets."),
            ("Customer Acquisition & Sales", "customer-acquisition", "Struggling to find paying customers beyond local neighborhood word-of-mouth."),
            ("Supply Chain & Raw Material Sourcing", "supply-chain", "Unreliable suppliers, transport spoilage, and fluctuating wholesale costs."),
            ("Business Planning & Growth Strategy", "business-planning", "Uncertain how to expand into the next district, scale team, or raise capital."),
            ("Digital Visibility & E-commerce", "digital-visibility", "Quality physical product but low online traction and poor digital discovery."),
            ("Packaging & Shelf Life", "packaging-shelflife", "Product degradation during transit and finding affordable food-grade packaging."),
        ]

        category_objs = {}
        for name, slug, desc in categories_data:
            obj, _ = ProblemCategory.objects.get_or_create(slug=slug, defaults={'name': name, 'description': desc})
            category_objs[slug] = obj

        # 3. Create Admin User
        admin_user, _ = User.objects.get_or_create(
            username='admin_demo',
            defaults={
                'email': 'admin@fem.network',
                'first_name': 'Siddharth',
                'last_name': 'Mehta',
                'role': User.Role.ADMIN,
                'city': 'Bengaluru',
                'region': 'Karnataka',
                'is_staff': True,
                'is_superuser': True,
                'bio': 'Platform Director & Ecosystem Architect for FEM.'
            }
        )
        admin_user.set_password('demo1234')
        admin_user.save()

        # 4. Create Mentors
        mentors_data = [
            {
                'username': 'mentor_demo',
                'email': 'rahul.patil@fem.network',
                'first_name': 'Dr. Rahul',
                'last_name': 'Patil',
                'city': 'Pune',
                'region': 'Maharashtra',
                'avatar_url': 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=400&q=80',
                'title': 'Senior Financial Strategist & Rural Enterprise Advisor',
                'bio': 'Over 18 years helping regional manufacturers and agri-enterprises overcome working capital dry spells, design resilient pricing models, and restructure debt.',
                'years_of_experience': 18,
                'rural_exp': True,
                'rural_count': 12,
                'industry': 'Agri-Business & Manufacturing Finance',
                'expertises': ['finance-cash-flow', 'business-planning', 'rural-enterprise'],
                'credits': {'entrepreneurs_mentored': 47, 'mentoring_hours': 32, 'rural_businesses_supported': 12, 'successful_outcomes': 18, 'community_contributions': 34, 'helpful_answers': 52, 'rating': 4.9},
                'experiences': [
                    ("Agri-Food Processing", "Cash Flow Management", "Helped a 4-year-old organic spice mill resolve a 60-day receivables deficit by renegotiating milestone terms with wholesale distributors.", "Converted a $40k quarterly operating deficit into a 19% positive cash cushion within 6 months.", 6, True),
                    ("Handloom & Textiles", "Pricing Strategy", "Guided handloom collective to transition from wholesale discount pricing to direct tier-1 boutique pricing with transparent craft storytelling.", "Doubled gross unit margins from 18% to 42%.", 4, True),
                    ("Rural Logistics", "Working Capital Optimization", "Designed a rolling receivables buffer and fuel-hedging agreement for a 12-vehicle rural fleet.", "Prevented insolvency during seasonal fuel price surges.", 5, True),
                ],
                'slots': [('MON', '10:00:00', '11:00:00', 'Cash Flow Diagnostic (45 min)'), ('THU', '15:00:00', '16:00:00', 'Financial Strategy Review (45 min)')]
            },
            {
                'username': 'priya_sharma',
                'email': 'priya.sharma@fem.network',
                'first_name': 'Priya',
                'last_name': 'Sharma',
                'city': 'Jaipur',
                'region': 'Rajasthan',
                'avatar_url': 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=400&q=80',
                'title': 'Brand & Customer Acquisition Specialist',
                'bio': 'Specialized in taking regional artisan, heritage food, and agricultural brands from zero to national direct-to-consumer presence without massive marketing budgets.',
                'years_of_experience': 14,
                'rural_exp': True,
                'rural_count': 22,
                'industry': 'D2C Consumer Goods & Heritage Crafts',
                'expertises': ['marketing-acquisition', 'branding-packaging', 'ecommerce-digital'],
                'credits': {'entrepreneurs_mentored': 38, 'mentoring_hours': 28, 'rural_businesses_supported': 22, 'successful_outcomes': 15, 'community_contributions': 29, 'helpful_answers': 41, 'rating': 4.95},
                'experiences': [
                    ("Rural Artisanal Foods", "Customer Acquisition & E-commerce", "Repositioned a village honey cooperative into an unadulterated forest honey brand with QR code batch traceability.", "Grew direct online orders from 20/month to over 1,400/month across 14 cities.", 5, True),
                    ("Natural Cosmetics", "Packaging & Shelf Discovery", "Redesigned packaging using biodegradable sugarcane pulp containers with elegant minimalist botanical labels.", "Achieved 72% repeat order rate and secured shelf space in 35 premium organic grocers.", 4, True),
                ],
                'slots': [('TUE', '14:00:00', '15:00:00', 'Brand & Positioning Audit (45 min)'), ('FRI', '11:00:00', '12:00:00', 'Customer Acquisition Strategy (45 min)')]
            },
            {
                'username': 'vikram_mehta',
                'email': 'vikram.mehta@fem.network',
                'first_name': 'Vikram',
                'last_name': 'Mehta',
                'city': 'Ahmedabad',
                'region': 'Gujarat',
                'avatar_url': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=400&q=80',
                'title': 'Supply Chain & Manufacturing Operations Lead',
                'bio': '20+ years setting up lean food processing facilities, cold storage networks, and vendor sourcing agreements for rural and semi-urban enterprises.',
                'years_of_experience': 22,
                'rural_exp': True,
                'rural_count': 16,
                'industry': 'Food Processing & Cold Chain Logistics',
                'expertises': ['supply-chain-ops', 'food-processing', 'rural-enterprise'],
                'credits': {'entrepreneurs_mentored': 52, 'mentoring_hours': 41, 'rural_businesses_supported': 16, 'successful_outcomes': 24, 'community_contributions': 19, 'helpful_answers': 36, 'rating': 4.88},
                'experiences': [
                    ("Dairy & Beverage", "Supply Chain Spoilage Reduction", "Installed localized solar chilling units and optimized collection route timing for 32 milk farmers.", "Cut milk spoilage losses from 14% to under 0.8% annually.", 7, True),
                    ("Edible Oil Refining", "Batch Scaling & Equipment Setup", "Guided small-scale cold-press oil producer to scale output 5x without losing cold-pressed purity certification.", "Reduced per-liter production cost by 28%.", 6, True),
                ],
                'slots': [('WED', '16:00:00', '17:00:00', 'Supply Chain Diagnostic (45 min)'), ('SAT', '10:00:00', '11:00:00', 'Production Efficiency Session (45 min)')]
            },
            {
                'username': 'ananya_roy',
                'email': 'ananya.roy@fem.network',
                'first_name': 'Ananya',
                'last_name': 'Roy',
                'city': 'Kolkata',
                'region': 'West Bengal',
                'avatar_url': 'https://images.unsplash.com/photo-1580489944761-15a19d654956?auto=format&fit=crop&w=400&q=80',
                'title': 'Fundraising, Grants & Growth Strategist',
                'bio': 'Helps grassroots and regional founders craft defensible business plans, clear financial projections, and pitch narratives that secure angel capital and commercial bank loans.',
                'years_of_experience': 12,
                'rural_exp': True,
                'rural_count': 19,
                'industry': 'Impact Investment & Enterprise Finance',
                'expertises': ['fundraising-grants', 'business-planning', 'finance-cash-flow'],
                'credits': {'entrepreneurs_mentored': 29, 'mentoring_hours': 22, 'rural_businesses_supported': 19, 'successful_outcomes': 14, 'community_contributions': 22, 'helpful_answers': 31, 'rating': 4.92},
                'experiences': [
                    ("Agritech Equipment", "Seed Funding Preparation", "Structured pitch model and financial unit economics for a low-cost solar dryer manufacturing startup.", "Secured $120,000 in early-stage equity funding and $45,000 in non-dilutive green innovation grant.", 5, True),
                ],
                'slots': [('THU', '11:00:00', '12:00:00', 'Pitch & Business Plan Diagnostic (45 min)')]
            }
        ]

        mentor_profile_objs = {}
        for m_data in mentors_data:
            user, _ = User.objects.get_or_create(
                username=m_data['username'],
                defaults={
                    'email': m_data['email'],
                    'first_name': m_data['first_name'],
                    'last_name': m_data['last_name'],
                    'role': User.Role.MENTOR,
                    'city': m_data['city'],
                    'region': m_data['region'],
                    'avatar_url': m_data['avatar_url'],
                    'bio': m_data['bio'],
                }
            )
            user.set_password('demo1234')
            user.save()

            m_profile, _ = MentorProfile.objects.get_or_create(
                user=user,
                defaults={
                    'professional_title': m_data['title'],
                    'biography': m_data['bio'],
                    'years_of_experience': m_data['years_of_experience'],
                    'rural_business_experience': m_data['rural_exp'],
                    'rural_businesses_count': m_data['rural_count'],
                    'primary_industry': m_data['industry'],
                    'verification_status': 'VERIFIED',
                    'is_accepting_mentees': True
                }
            )
            mentor_profile_objs[m_data['username']] = m_profile

            # Assign expertises
            for exp_slug in m_data['expertises']:
                if exp_slug in expertise_objs:
                    m_profile.expertises.add(expertise_objs[exp_slug])

            # Mentor Credits
            c_info = m_data['credits']
            MentorCredit.objects.update_or_create(
                mentor=m_profile,
                defaults={
                    'entrepreneurs_mentored': c_info['entrepreneurs_mentored'],
                    'mentoring_hours': c_info['mentoring_hours'],
                    'rural_businesses_supported': c_info['rural_businesses_supported'],
                    'successful_outcomes': c_info['successful_outcomes'],
                    'community_contributions': c_info['community_contributions'],
                    'helpful_answers': c_info['helpful_answers'],
                    'positive_feedback_rating': c_info['rating']
                }
            )

            # Experiences
            for ind, ptype, desc, outcome, yexp, rfocused in m_data['experiences']:
                MentorExperience.objects.get_or_create(
                    mentor=m_profile,
                    problem_type=ptype,
                    defaults={
                        'industry': ind,
                        'description': desc,
                        'outcome': outcome,
                        'years_of_experience': yexp,
                        'is_rural_focused': rfocused
                    }
                )

            # Availability Slots
            for day, start, end, stype in m_data['slots']:
                AvailabilitySlot.objects.get_or_create(
                    mentor=m_profile,
                    day_of_week=day,
                    start_time=start,
                    end_time=end,
                    defaults={'slot_type': stype, 'is_active': True}
                )

        # 5. Create Entrepreneurs
        entrepreneurs_data = [
            {
                'username': 'entrepreneur_demo',
                'email': 'aarav.deshmukh@fem.network',
                'first_name': 'Aarav',
                'last_name': 'Deshmukh',
                'city': 'Nashik',
                'region': 'Maharashtra',
                'avatar_url': 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=400&q=80',
                'bio': 'Founder of Satva Organics. Processing organic millets and cold-pressed edible oils directly sourced from 40 smallholder farming families.',
                'business_name': 'Satva Organics',
                'industry': 'Agri-Food & Value-Added Processing',
                'stage': 'EARLY',
                'location': 'Nashik, Maharashtra',
                'is_rural': True,
                'desc': 'We produce chemical-free, nutrient-rich finger millet and cold-pressed sesame oil. Growing fast in local retail but facing steep cash flow gaps due to distributor payment cycles.',
                'skills': 'Raw Grain Sourcing, Cold Press Operations, Quality Audits',
                'collab': 'Seeking sustainable packaging vendors and regional logistics aggregation partners.',
            },
            {
                'username': 'sunita_rao',
                'email': 'sunita.rao@fem.network',
                'first_name': 'Sunita',
                'last_name': 'Rao',
                'city': 'Hubli',
                'region': 'Karnataka',
                'avatar_url': 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=400&q=80',
                'bio': 'Co-founder of Vanya Crafts. Championing natural-dye handloom fabrics woven by 65 village women artisans.',
                'business_name': 'Vanya Crafts Collective',
                'industry': 'Handloom, Textiles & Sustainable Apparel',
                'stage': 'GROWTH',
                'location': 'Hubli, Karnataka',
                'is_rural': True,
                'desc': 'We create hand-spun cotton and plant-dyed apparel. Our quality is world-class, but our digital visibility and direct online customer acquisition need strategic transformation.',
                'skills': 'Natural Indigo Dyeing, Loom Coordination, Design Curation',
                'collab': 'Looking for ethical fashion retail partners and digital storytelling collaborators.',
            }
        ]

        entrepreneur_users = {}
        for e_data in entrepreneurs_data:
            user, _ = User.objects.get_or_create(
                username=e_data['username'],
                defaults={
                    'email': e_data['email'],
                    'first_name': e_data['first_name'],
                    'last_name': e_data['last_name'],
                    'role': User.Role.ENTREPRENEUR,
                    'city': e_data['city'],
                    'region': e_data['region'],
                    'avatar_url': e_data['avatar_url'],
                    'bio': e_data['bio'],
                }
            )
            user.set_password('demo1234')
            user.save()
            entrepreneur_users[e_data['username']] = user

            EntrepreneurProfile.objects.update_or_create(
                user=user,
                defaults={
                    'business_name': e_data['business_name'],
                    'industry': e_data['industry'],
                    'business_stage': e_data['stage'],
                    'location': e_data['location'],
                    'is_rural_business': e_data['is_rural'],
                    'description': e_data['desc'],
                    'skills': e_data['skills'],
                    'collaboration_interests': e_data['collab']
                }
            )

        # 6. Create Seed Problems & Run Intelligent Matching
        demo_user = entrepreneur_users['entrepreneur_demo']
        problem_1, _ = Problem.objects.get_or_create(
            entrepreneur=demo_user,
            title="Severe Cash Flow Deficits from 60-Day Distributor Payment Delays",
            defaults={
                'description': "My rural organic food processing business produces cold-pressed sesame oil and millet flour. We have solid demand from regional retailers, but distributors hold payments for 60 to 75 days. Meanwhile, our smallholder farmers must be paid cash upfront at harvest. This creates a recurring $35,000 working capital deficit where we struggle to purchase inventory for the next production cycle.",
                'category': category_objs.get('cash-flow'),
                'industry': 'Agri-Food & Value-Added Processing',
                'business_stage': 'Early Stage / Initial Sales',
                'urgency': 'CRITICAL',
                'desired_support': 'Cash flow forecasting, working capital restructuring, distributor contract terms',
                'is_rural_business': True,
                'location': 'Nashik, Maharashtra',
                'status': 'OPEN'
            }
        )
        # Run matching engine on Problem 1
        matches = run_matching_engine_for_problem(problem_1)
        self.stdout.write(f"Generated {len(matches)} mentor matches for problem: {problem_1.title}")

        # Problem 2
        sunita_user = entrepreneur_users['sunita_rao']
        problem_2, _ = Problem.objects.get_or_create(
            entrepreneur=sunita_user,
            title="Low Digital Visibility and Ineffective Customer Acquisition for Handloom Products",
            defaults={
                'description': "We represent 65 women handloom weavers producing exquisite natural-dyed textiles. While exhibition visitors love our products, our direct online store barely gets 10 orders a week. Our previous social media ad campaign burned through budget with virtually no qualified customer conversions.",
                'category': category_objs.get('customer-acquisition'),
                'industry': 'Handloom & Sustainable Crafts',
                'business_stage': 'Growth Stage',
                'urgency': 'HIGH',
                'desired_support': 'D2C brand storytelling, digital customer acquisition channels, pricing psychology',
                'is_rural_business': True,
                'location': 'Hubli, Karnataka',
                'status': 'OPEN'
            }
        )
        run_matching_engine_for_problem(problem_2)

        # 7. Mentoring Request & Session
        rahul_mentor = mentor_profile_objs['mentor_demo']
        req, _ = MentoringRequest.objects.get_or_create(
            problem=problem_1,
            entrepreneur=demo_user,
            mentor=rahul_mentor,
            defaults={
                'message': "Hello Dr. Rahul, I reviewed your extensive background helping regional food processors resolve distributor payment crunches. Our sesame oil business is currently trapped in a 65-day payment gap. I would deeply value your diagnostic review on structuring invoice milestones.",
                'status': 'ACCEPTED'
            }
        )
        MentoringSession.objects.get_or_create(
            request=req,
            defaults={
                'scheduled_at': timezone.now() + datetime.timedelta(days=2, hours=3),
                'duration_minutes': 45,
                'status': 'SCHEDULED',
                'meeting_link': 'https://fem.network/rooms/session-diagnostic-4401',
                'mentor_notes': 'Entrepreneur has strong product unit margin (42%) but zero receivables buffer. Will review rolling cash flow template and distributor contract clauses.',
            }
        )

        # 8. Collaboration Requests
        collabs_data = [
            {
                'user': demo_user,
                'title': "Seeking Sustainable Packaging Supplier for Cold-Pressed Edible Oils",
                'desc': "We need 500ml and 1L dark glass bottles or food-grade tin containers with tamper-evident caps. Monthly volume: 2,500 units. Must be able to deliver to Nashik region at competitive small-batch rates.",
                'industry': 'Food & Agriculture',
                'collab_type': 'PACKAGING',
                'location': 'Maharashtra / Karnataka',
                'tags': 'Packaging, Cold-Pressed Oil, Rural Enterprise, Eco-Friendly'
            },
            {
                'user': sunita_user,
                'title': "Looking for Boutique Organic Retailers to Stock Hand-Spun Natural Linen",
                'desc': "We produce certified natural indigo and madder-root dyed cotton fabric and home linen. Offering favorable consignment margins (35%) to curated design stores and sustainable lifestyle boutiques.",
                'industry': 'Textiles & Handloom',
                'collab_type': 'DISTRIBUTION',
                'location': 'Metro & Tier-1 Regional Cities',
                'tags': 'Handloom, Sustainable Apparel, Boutique Retail, Consignment'
            },
            {
                'user': demo_user,
                'title': "Joint Cold Storage Aggregation for Regional Farmers in North Maharashtra",
                'desc': "We are pooling demand to negotiate 40% bulk discount on temperature-controlled warehouse space for grain and seed preservation. Need 2 other agri-producers to join consortium.",
                'industry': 'Supply Chain & Logistics',
                'collab_type': 'SHARED_RESOURCES',
                'location': 'Nashik & Surrounding Talukas',
                'tags': 'Cold Storage, Aggregation, Sourcing, Cost Sharing'
            }
        ]
        for c in collabs_data:
            CollaborationRequest.objects.get_or_create(
                entrepreneur=c['user'],
                title=c['title'],
                defaults={
                    'description': c['desc'],
                    'industry': c['industry'],
                    'collaboration_type': c['collab_type'],
                    'location': c['location'],
                    'tags': c['tags'],
                    'status': 'OPEN'
                }
            )

        # 9. Success & Failure Stories
        stories_data = [
            {
                'author': demo_user,
                'type': 'FAILURE',
                'title': "Why Our First Retail Supermarket Launch Nearly Destroyed Our Business",
                'context': "Organic Cold-Pressed Edible Oils, Year 2",
                'summary': "We celebrated signing our first 15-supermarket retail deal, only to realize that listing fees, 90-day credit, and damaged stock returns crippled our entire production cash flow.",
                'happened': "In 2024, a regional supermarket chain offered to stock our sesame and groundnut oils across 15 stores. We borrowed capital to produce 4,000 units. However, they demanded a 20% slotting fee, paid on a 90-day cycle, and arbitrarily returned dented bottles at our expense. Our cash was tied up on their shelves while our farmer suppliers were waiting for cash. We came within 10 days of missing payroll.",
                'learned': "High gross retail placement without high velocity or upfront trade credit terms is dangerous for a bootstrapping producer. Supermarkets shift 100% of the working capital risk onto small suppliers.",
                'would_differently': "I will never accept 90-day credit terms again without invoice factoring or a guaranteed weekly sales-volume minimum. We now prioritize direct institutional buyers (restaurants, organic bakeries) who pay within 15 days.",
                'takeaway': "Revenue on an invoice is not cash in the bank. Always calculate your cash conversion cycle before saying yes to large retail distribution.",
                'likes': 42
            },
            {
                'author': mentor_profile_objs['mentor_demo'].user,
                'type': 'SUCCESS',
                'title': "How Restructuring Milestone Contracts Saved a Rural Spice Cooperative",
                'context': "Farm Cooperative Turnaround | 120 Member Farmers",
                'summary': "By replacing standard 60-day credit with 30% upfront harvest commitment and 70% delivery escrow, we turned an operating deficit into a 22% surplus.",
                'happened': "A 120-member turmeric cooperative was facing collapse because institutional spice buyers were constantly delaying final payouts post-processing. We worked together to audit their buyer tiering, identified the top 4 most reliable corporate buyers, and presented a new contract: buyers who locked in harvest volumes with 30% advance received guaranteed Grade-A purity and prioritized batch testing.",
                'learned': "Quality reliability is a powerful bargaining chip. B2B corporate buyers are often willing to provide working capital advances if it guarantees uninterrupted raw material supply with verified lab purity.",
                'would_differently': "Instituted this contract model 2 years earlier instead of tolerating predatory delay tactics from predatory middle-tier brokers.",
                'takeaway': "When you guarantee uncompromised quality and traceability, you have the leverage to negotiate payment terms that protect your liquidity.",
                'likes': 68
            },
            {
                'author': sunita_user,
                'type': 'FAILURE',
                'title': "The Expensive Mistake of Discounting Heritage Craftsmanship",
                'context': "Handloom Weavers Collective, Year 3",
                'summary': "Thinking low prices would attract mainstream customers, we underpriced our natural indigo textiles by 40% and attracted bargain hunters while alienating true craft collectors.",
                'happened': "Early in our journey, we felt intimidated by high-end prices in metro craft stores. We priced our hand-spun shawls at only $18, barely covering artisan labor. Instead of increasing sales volume, customers questioned whether our natural indigo was genuine, assuming the low price meant synthetic chemical dye. Meanwhile, our weavers felt demoralized.",
                'learned': "In artisan and heritage products, price is a signal of authenticity and dignity. Underpricing destroys the perceived value of genuine slow craftsmanship.",
                'would_differently': "Document the 14-day dyeing process with artisan video documentation, price with healthy 50%+ gross margins, and sell exclusively to customers who value ethical provenance.",
                'takeaway': "Never compete on price when your true competitive advantage is craftsmanship, heritage, and human dignity.",
                'likes': 56
            }
        ]

        for s in stories_data:
            Story.objects.get_or_create(
                author=s['author'],
                title=s['title'],
                defaults={
                    'story_type': s['type'],
                    'business_context': s['context'],
                    'summary': s['summary'],
                    'what_happened': s['happened'],
                    'what_i_learned': s['learned'],
                    'what_i_would_do_differently': s['would_differently'],
                    'key_takeaway': s['takeaway'],
                    'likes_count': s['likes'],
                    'is_approved': True
                }
            )

        # 10. Community Posts
        posts_data = [
            {
                'author': demo_user,
                'type': 'QUESTION',
                'title': "How do rural food businesses handle distributor credit without risking cash insolvency?",
                'content': "We supply to 18 retail outlets across two districts. Over the last three months, average receivables have stretched from 30 days to 68 days. We want to know: what clauses or incentives do fellow entrepreneurs use to ensure on-time invoice settlement without losing retail shelf space?",
                'tags': 'CashFlow, Distribution, Retail, ContractTerms',
                'likes': 19,
                'comments': [
                    (mentor_profile_objs['mentor_demo'].user, "A practical approach that works wonders: Offer a 2.5% prompt settlement cash discount if settled within 10 days. Also, place a hard credit limit (e.g. $1,500) where next batch dispatch is strictly frozen until older invoices are cleared."),
                    (sunita_user, "We implemented Dr. Rahul's credit limit rule last year. Two habitual late-payers walked away, but the remaining 14 distributors now pay strictly on time!"),
                ]
            },
            {
                'author': mentor_profile_objs['priya_sharma'].user,
                'type': 'ADVICE',
                'title': "3 Low-Cost Customer Acquisition Tactics for Regional Artisanal Brands",
                'content': "Having guided 38 regional brands, here is what actually moves the needle when you don't have venture capital for ads:\n1. Unboxing Experience & QR Storytelling: Put a personal note inside every box with a direct WhatsApp number for feedback.\n2. Hyper-Local Sampling Partnerships: Place tasting or sample counters inside complementary premium stores (e.g., honey inside specialty tea cafes).\n3. B2B Corporate Gifting Catalogs: October to January corporate festival gifting delivers 40% of annual revenue with upfront 50% bank deposits.",
                'tags': 'CustomerAcquisition, D2C, Branding, GrowthStrategy',
                'likes': 38,
                'comments': [
                    (demo_user, "The corporate gifting catalog idea is brilliant! We have 200kg of cold-pressed gift sets ready for upcoming regional festivals."),
                ]
            },
            {
                'author': mentor_profile_objs['vikram_mehta'].user,
                'type': 'RESOURCE',
                'title': "Standard Operating Checklist for Small-Batch Food Processing Facilities",
                'content': "I have compiled a 12-point quality, sanitation, and temperature log sheet that small rural food producers can print and pin to their processing room wall. It prevents 90% of routine batch rejections and contamination issues during regulatory inspections.",
                'tags': 'FoodProcessing, QualityControl, Operations, StandardOperatingProcedures',
                'likes': 27,
                'comments': []
            }
        ]

        for p_data in posts_data:
            post, _ = CommunityPost.objects.get_or_create(
                author=p_data['author'],
                title=p_data['title'],
                defaults={
                    'post_type': p_data['type'],
                    'content': p_data['content'],
                    'tags': p_data['tags'],
                    'likes_count': p_data['likes']
                }
            )
            for c_author, c_text in p_data['comments']:
                Comment.objects.get_or_create(post=post, author=c_author, content=c_text)

        # 11. Conversation & Messages
        conv, _ = Conversation.get_or_create_conversation(
            demo_user,
            mentor_profile_objs['mentor_demo'].user,
            subject="Diagnostic regarding 60-day distributor receivables"
        )
        msg_1, _ = Message.objects.get_or_create(
            conversation=conv,
            sender=demo_user,
            content="Hello Dr. Rahul, thank you for accepting our mentorship request! I've uploaded our recent 3-month distributor sales log for your review.",
            defaults={'read_status': True, 'sync_status': 'SYNCED'}
        )
        msg_2, _ = Message.objects.get_or_create(
            conversation=conv,
            sender=mentor_profile_objs['mentor_demo'].user,
            content="Good evening Aarav. I reviewed your problem statement and sales numbers. Your unit margins are very healthy at 42%, which means the business model itself is sound—it's purely a working capital duration mismatch. Looking forward to our diagnostic call on Thursday.",
            defaults={'read_status': True, 'sync_status': 'SYNCED'}
        )

        # 12. Notifications
        Notification.objects.get_or_create(
            recipient=demo_user,
            title="Dr. Rahul Patil accepted your mentoring request",
            defaults={
                'notification_type': 'REQUEST_ACCEPTED',
                'message': "Dr. Rahul Patil accepted your request regarding 'Severe Cash Flow Deficits'. Your diagnostic session is scheduled.",
                'action_url': '/entrepreneur/problems/',
                'read_status': False
            }
        )
        Notification.objects.get_or_create(
            recipient=demo_user,
            title="New Mentor Recommendations Generated",
            defaults={
                'notification_type': 'RECOMMENDATION',
                'message': "The matching engine identified 3 verified mentors with experience solving similar cash flow bottlenecks.",
                'action_url': f'/entrepreneur/problems/{problem_1.id}/matches/',
                'read_status': False
            }
        )

        self.stdout.write(self.style.SUCCESS("[OK] Successfully populated FEM ecosystem with verified mentors, real problems, matches, stories, community posts, and sessions!"))
