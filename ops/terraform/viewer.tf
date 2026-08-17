# The trajectory viewer.
#
# `harbor view` is a web server over a folder of job directories, so pointing it
# at the shared filesystem gives every participant the same trajectory UI they
# have locally, over the graded runs. It reads `runs/`, where the worker writes
# one directory per rollout: the viewer treats each immediate child of its root
# as a job, and rejects any job path resolving outside that root, so the layout
# has to be genuinely flat rather than symlinked.
#
# It is NOT a read-only tool. The viewer ships POST /api/run and
# /api/run/pick-directory, which start Harbor runs and browse the filesystem.
# On a public hostname that is a remote execution surface, so /api/run* is
# refused at the load balancer and the task gets no Docker socket. The mount is
# read-only as well: three independent reasons a request cannot turn into a run.

resource "aws_lb_target_group" "viewer" {
  name        = "${local.name}-viewer"
  port        = 8080
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.default.id
  target_type = "ip"

  health_check {
    path    = "/api/health"
    matcher = "200"
  }
}

# Priority matters: the refusal has to be evaluated before the forward, or the
# forward matches first and the run API is reachable.
resource "aws_lb_listener_rule" "viewer_deny_run" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 10

  action {
    type = "fixed-response"
    fixed_response {
      content_type = "text/plain"
      status_code  = "403"
      message_body = "the viewer is read-only here"
    }
  }

  condition {
    host_header {
      values = [local.traces_fqdn]
    }
  }

  condition {
    path_pattern {
      values = ["/api/run", "/api/run/*"]
    }
  }
}

resource "aws_lb_listener_rule" "viewer" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 20

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.viewer.arn
  }

  condition {
    host_header {
      values = [local.traces_fqdn]
    }
  }
}

resource "aws_ecs_task_definition" "viewer" {
  family                   = "${local.name}-viewer"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]

  runtime_platform {
    cpu_architecture        = upper(var.image_architecture)
    operating_system_family = "LINUX"
  }

  cpu                = 512
  memory             = 1024
  execution_role_arn = aws_iam_role.execution.arn

  volume {
    name = "jobs"
    efs_volume_configuration {
      file_system_id     = aws_efs_file_system.jobs.id
      transit_encryption = "ENABLED"
      authorization_config {
        access_point_id = aws_efs_access_point.jobs.id
        iam             = "DISABLED"
      }
    }
  }

  container_definitions = jsonencode([{
    name      = "viewer"
    image     = "${aws_ecr_repository.worker.repository_url}:latest"
    essential = true
    # The worker image already carries harbor; a second image to run a second
    # entry point of the same package would be one more thing to keep in sync.
    # --no-build because the packaged viewer ships prebuilt static assets, and
    # a rebuild would want a Node toolchain that is not in this image.
    command = ["harbor", "view", "/app/jobs/runs", "--host", "0.0.0.0", "--port", "8080", "--no-build"]
    environment = [
      { name = "BENCHMARK_REGION", value = var.region },
    ]
    mountPoints  = [{ sourceVolume = "jobs", containerPath = "/app/jobs", readOnly = true }]
    portMappings = [{ containerPort = 8080 }]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.this["viewer"].name
        "awslogs-region"        = var.region
        "awslogs-stream-prefix" = "viewer"
      }
    }
  }])
}

resource "aws_ecs_service" "viewer" {
  name            = "viewer"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.viewer.arn
  desired_count   = var.viewer_replicas
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = local.subnets
    security_groups  = [aws_security_group.service.id]
    assign_public_ip = true # image pull without a NAT gateway
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.viewer.arn
    container_name   = "viewer"
    container_port   = 8080
  }

  depends_on = [aws_lb_listener.https]
}

variable "viewer_replicas" {
  description = "Trajectory viewer tasks. 0 turns the viewer off with the rest of the stack."
  type        = number
  default     = 1
}

output "traces_url" {
  value = "https://${local.traces_fqdn}"
}
