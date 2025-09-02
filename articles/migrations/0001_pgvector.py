from pgvector.django import vectorextension

class migration(migrations.migration):
    operations = [
        vectorextension()
    ]
