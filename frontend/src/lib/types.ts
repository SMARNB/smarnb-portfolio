/* =============================================================================
   API types — mirror backend/app/schemas.py exactly. The backend is the source
   of truth; these only describe the JSON it already returns/accepts.
   ========================================================================== */

export interface User {
  id: number;
  email: string;
  name: string;
  role: string; // "client" | "admin"
  whatsapp?: string;
  created_at: string;
}

export interface Token {
  access_token: string;
  token_type: string;
  user: User;
}

export interface OrderItem {
  service: string;
  tier: string;
  price: number;
  qty: number;
}

export interface OrderUpdate {
  message: string;
  status: string | null;
  progress: number | null;
  created_at: string;
}

export interface Deliverable {
  id: number;
  title: string;
  preview_url: string;
  final_url: string | null; // only present once the order is paid
  locked: boolean;
  note: string;
  created_at: string;
}

export interface Milestone {
  id: number;
  title: string;
  status_key: string; // one of STATUS_FLOW, or "" for custom steps
  done: boolean;
  done_at: string | null;
  sort_order: number;
}

export interface Order {
  public_id: string;
  customer_name: string;
  customer_email: string;
  customer_whatsapp: string;
  items: OrderItem[];
  total: number;
  status: string; // received|confirmed|in_progress|in_review|delivered|cancelled
  status_label: string;
  progress: number;
  due_date: string | null;
  notes: string;
  payment_method: string;
  payment_status: string; // unpaid|paid|refunded
  created_at: string;
  updated_at: string;
  updates: OrderUpdate[];
  deliverables: Deliverable[];
  milestones: Milestone[];
  next_step: string | null;
}

export interface OrderCreate {
  customer_name?: string;
  customer_email: string;
  customer_whatsapp?: string;
  notes?: string;
  payment_method?: string;
  items: OrderItem[];
}

export interface Stats {
  total_orders: number;
  active_orders: number;
  delivered_orders: number;
  revenue: number;
  clients: number;
  by_status: Record<string, number>;
}

export interface ServicePackage {
  tier: string;
  price: number;
  delivery: string;
  revisions: number;
  summary: string;
  features: string[];
  popular?: boolean;
}

export interface ServiceOut {
  id: number;
  slug: string;
  title: string;
  category: string;
  icon: string;
  short: string;
  tags: string[];
  packages: ServicePackage[];
  deliverables: string[];
  active: boolean;
  sort_order: number;
}

export interface PublicCatalog {
  managed: boolean;
  services: ServiceOut[];
}

export interface ServiceIn {
  title: string;
  category: string;
  icon: string;
  short: string;
  tags: string[];
  packages: ServicePackage[];
  deliverables: string[];
  active: boolean;
  sort_order: number;
  slug?: string | null;
}

export interface Testimonial {
  id: number;
  name: string;
  role: string;
  location: string;
  rating: number;
  text: string;
  created_at: string;
}

export interface TestimonialAdmin extends Testimonial {
  status: string; // pending|approved|rejected
}

export interface Attachment {
  id: number;
  filename: string;
  content_type: string;
  size: number;
}

export interface ChatMessage {
  id?: number;
  sender: string; // client|bot|dev
  body: string;
  created_at?: string;
  attachment?: Attachment | null;
}

export interface ChatThread {
  public_id: string;
  secret?: string | null;
  status: string;
  human_takeover: boolean;
  needs_human: boolean;
  messages: ChatMessage[];
  quick_replies: string[];
}

export interface ConversationSummary {
  public_id: string;
  customer_name: string;
  customer_email: string;
  last_message: string;
  last_message_at: string;
  unread: number;
  status: string;
  needs_human: boolean;
  human_takeover: boolean;
  channel?: string; // "web" | "whatsapp"
}

export interface BotKnowledge {
  id: number;
  question: string;
  answer: string;
  keywords: string;
  enabled: boolean;
  hits: number;
  created_at: string;
}

export interface BotUnanswered {
  id: number;
  question: string;
  count: number;
  resolved: boolean;
  created_at: string;
  last_seen: string;
}

export interface PaymentConfig {
  stripe_enabled: boolean;
  safepay_enabled?: boolean;
}

/* --- Blog ------------------------------------------------------------------- */
export interface BlogRelatedService {
  slug: string;
  title: string;
  short: string;
  category: string;
  icon: string;
  min_price: number | null;
}

export interface BlogPost {
  id: number;
  slug: string;
  title: string;
  excerpt: string;
  body_md?: string; // only on full (single/admin) responses
  body_html?: string; // only on full responses
  cover_image: string;
  category: string;
  tags: string[];
  related_services: string[]; // service slugs attached to the post
  related?: BlogRelatedService[]; // resolved services (single/admin full responses)
  status: string; // draft | published
  reading_minutes: number;
  published_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface BlogListResponse {
  categories: string[];
  posts: BlogPost[];
}

export interface BlogImageUpload {
  id: number;
  url: string;
  filename: string;
  content_type: string;
  size: number;
}

export interface BlogPreview {
  body_html: string;
  reading_minutes: number;
  excerpt: string;
}

/* --- SEO control centre (mirrors backend app/seo.py document) --------------- */
export interface SeoCrumb {
  name: string;
  path: string;
}

export interface SeoRouteMeta {
  title: string;
  description: string;
  canonical: string;
  robots: string;
  keywords: string;
  og_title: string;
  og_description: string;
  og_image: string;
  twitter_title: string;
  twitter_description: string;
  twitter_image: string;
  breadcrumb: SeoCrumb[];
}

export interface SeoJsonLd {
  person: boolean;
  services: boolean;
  reviews: boolean;
  faq: boolean;
  breadcrumb: boolean;
  website: boolean;
  search_action: boolean;
}

export interface SeoGeneral {
  site_name: string;
  brand_name: string;
  base_url: string;
  title_template: string;
  default_title: string;
  default_description: string;
  default_keywords: string;
  author: string;
  locale: string;
  language: string;
  default_og_image: string;
  og_type: string;
  twitter_card: string;
  twitter_site: string;
  twitter_creator: string;
  theme_color: string;
  robots_default: string;
  google_verification: string;
  bing_verification: string;
  yandex_verification: string;
  ga4_id: string;
  gtm_id: string;
  google_ads_id: string;
  meta_pixel_id: string;
  meta_domain_verification: string;
  person_name: string;
  job_title: string;
  org_type: string;
  email: string;
  telephone: string;
  whatsapp: string;
  area_served: string;
  price_range: string;
  logo: string;
  image: string;
  same_as: string[];
  favicon: string;
  manifest: string;
  jsonld: SeoJsonLd;
  robots_txt: string;
  sitemap_changefreq: string;
  target_keywords: string;
}

export interface SeoFaqItem {
  q: string;
  a: string;
}

export interface SeoDoc {
  general: SeoGeneral;
  routes: Record<string, SeoRouteMeta>;
  faq: SeoFaqItem[];
}

/** Error thrown by the API client; carries the HTTP status. */
export interface ApiError extends Error {
  status?: number;
}
