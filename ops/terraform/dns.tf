# A real name and a real certificate.
#
# The load balancer's own hostname is fine for a smoke test but wrong to hand
# to participants, and plain HTTP is wrong the moment anything resembling a
# credential crosses it. ACM validates through DNS in the same zone Terraform
# reads, so the certificate issues without anyone clicking anything.

data "aws_route53_zone" "public" {
  name = var.dns_zone
}

resource "aws_acm_certificate" "dashboard" {
  domain_name = local.dashboard_fqdn
  # The viewer is a second hostname rather than a path on the first: its assets
  # are absolute (/assets/...), so serving it under a prefix would 404 every one
  # of them. One certificate covers both.
  subject_alternative_names = [local.traces_fqdn, local.gateway_fqdn]
  validation_method         = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_route53_record" "cert_validation" {
  for_each = {
    for option in aws_acm_certificate.dashboard.domain_validation_options :
    option.domain_name => {
      name   = option.resource_record_name
      record = option.resource_record_value
      type   = option.resource_record_type
    }
  }

  zone_id         = data.aws_route53_zone.public.zone_id
  name            = each.value.name
  type            = each.value.type
  records         = [each.value.record]
  ttl             = 60
  allow_overwrite = true
}

resource "aws_acm_certificate_validation" "dashboard" {
  certificate_arn         = aws_acm_certificate.dashboard.arn
  validation_record_fqdns = [for r in aws_route53_record.cert_validation : r.fqdn]
}

resource "aws_route53_record" "dashboard" {
  zone_id = data.aws_route53_zone.public.zone_id
  name    = local.dashboard_fqdn
  type    = "A"

  alias {
    name                   = aws_lb.dashboard.dns_name
    zone_id                = aws_lb.dashboard.zone_id
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "traces" {
  zone_id = data.aws_route53_zone.public.zone_id
  name    = local.traces_fqdn
  type    = "A"

  alias {
    name                   = aws_lb.dashboard.dns_name
    zone_id                = aws_lb.dashboard.zone_id
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "gateway" {
  zone_id = data.aws_route53_zone.public.zone_id
  name    = local.gateway_fqdn
  type    = "A"

  alias {
    name                   = aws_lb.dashboard.dns_name
    zone_id                = aws_lb.dashboard.zone_id
    evaluate_target_health = true
  }
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.dashboard.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = aws_acm_certificate_validation.dashboard.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }
}

output "dashboard_https" {
  value = "https://${local.dashboard_fqdn}"
}
