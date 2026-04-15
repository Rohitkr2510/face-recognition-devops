output "instance_public_ip" {
  value = aws_instance.face_service.public_ip
}

output "instance_id" {
  value = aws_instance.face_service.id
}
