export type BiasLean = "left" | "center" | "right";

export interface Article {
  id: string;
  title: string;
  source: string;
  date: string;
  tag: HashTag;
  image: string;
  bias: number;
  lean: BiasLean;
  href: string;
}

export type HashTag =
  | "politics"
  | "conflict"
  | "environment"
  | "finance"
  | "sports";

export interface NavItem {
  label: string;
  href: string;
}

export type TimelineBucket = "Today" | "Yesterday" | "This Week" | "This Month";

export interface FooterSection {
  title: string;
  links: { label: string; href: string }[];
}
