# Performance & Security Guidelines

**Last Updated:** 2026-02-07

---

## Performance Guidelines

### Backend Optimization

#### Database Queries

**Avoid N+1 queries:**
```python
# Bad: N+1 problem
leaves = LeaveRequest.objects.all()
for leave in leaves:
    print(leave.user.email)  # Query per iteration

# Good: Use select_related for ForeignKey
leaves = LeaveRequest.objects.select_related(
    'user', 'category', 'approved_by'
).all()

# Good: Use prefetch_related for ManyToMany/reverse ForeignKey
departments = Department.objects.prefetch_related('managers').all()

# Good: Limit fields for better performance
users = User.objects.filter(
    is_active=True
).values_list('id', 'email', 'name')
```

**Query Optimization:**
- Use `.only()` and `.defer()` to limit fields
- Use `.exists()` instead of `.count()` for boolean checks
- Use `.bulk_create()` for multiple inserts
- Use `.bulk_update()` for multiple updates
- Add database indexes on frequently filtered fields

#### Caching Strategy (Future)

```python
from django.core.cache import cache

def get_user_balance(user_id, category):
    # Try cache first
    cache_key = f"balance:{user_id}:{category}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    # Query database
    balance = LeaveBalance.objects.get(
        user_id=user_id,
        category=category
    )

    # Cache for 1 hour
    cache.set(cache_key, balance, timeout=3600)
    return balance
```

#### API Optimization

**Pagination:**
```python
from rest_framework.pagination import PageNumberPagination

class StandardPageNumberPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class LeaveRequestViewSet(viewsets.ModelViewSet):
    pagination_class = StandardPageNumberPagination
```

**Filtering:**
```python
from django_filters import FilterSet, CharFilter, DateFromToRangeFilter

class LeaveRequestFilter(FilterSet):
    status = CharFilter(field_name='status', lookup_expr='exact')
    date_range = DateFromToRangeFilter(field_name='start_date')

    class Meta:
        model = LeaveRequest
        fields = ['user', 'status', 'date_range']

# In viewset
class LeaveRequestViewSet(viewsets.ModelViewSet):
    filterset_class = LeaveRequestFilter
```

**Serializer Optimization:**
```python
class LeaveRequestSerializer(serializers.ModelSerializer):
    # Avoid expensive nested serializers for list view
    class Meta:
        model = LeaveRequest
        fields = ['id', 'user_id', 'status', 'start_date']

class LeaveRequestDetailedSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)

    class Meta:
        model = LeaveRequest
        fields = ['id', 'user', 'category', 'status', 'notes']
```

#### API Response Targets

- **API Response Time:** < 500ms (99th percentile)
- **Page Load Time:** < 3 seconds
- **Database Query:** < 100ms per request
- **Concurrent Users:** Support 100+

---

### Frontend Optimization

#### Code Splitting

```typescript
// Lazy load heavy components
const Dashboard = React.lazy(() => import('./pages/Dashboard'));
const Analytics = React.lazy(() => import('./pages/Analytics'));

// Use Suspense
<Suspense fallback={<Spinner />}>
  <Routes>
    <Route path="/dashboard" element={<Dashboard />} />
    <Route path="/analytics" element={<Analytics />} />
  </Routes>
</Suspense>
```

#### Memoization

```typescript
// Memoize components to prevent unnecessary re-renders
const LeaveCard = React.memo(({ leave, onClick }) => {
  return <Card onClick={onClick}>{leave.id}</Card>;
});

// Memoize expensive computations
const ExpensiveComponent = ({ data }) => {
  const result = useMemo(() => {
    return expensiveCalculation(data);
  }, [data]);

  return <div>{result}</div>;
};
```

#### Callback Optimization

```typescript
// Debounce search input
const useDebounce = (value: string, delay: number) => {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(handler);
  }, [value, delay]);

  return debouncedValue;
};

const SearchComponent = () => {
  const [search, setSearch] = useState('');
  const debouncedSearch = useDebounce(search, 500);

  useEffect(() => {
    // Only call API after user stops typing
    searchApi.search(debouncedSearch);
  }, [debouncedSearch]);

  return <Input value={search} onChange={(e) => setSearch(e.target.value)} />;
};
```

#### Bundle Size

- **Target:** < 300KB (gzipped)
- **Check:** `npm run build && du -sh dist/`
- **Analyze:** Use `source-map-explorer`

---

## Security Guidelines

### Authentication & Authorization

#### JWT Best Practices

```python
# Good: Use separate access and refresh tokens
ACCESS_TOKEN_LIFETIME = 3600  # 1 hour
REFRESH_TOKEN_LIFETIME = 604800  # 7 days

# Token blacklist on logout
class LogoutView(APIView):
    def post(self, request):
        refresh = request.data.get('refresh')
        token = RefreshToken(refresh)
        token.blacklist()
        return Response(status=status.HTTP_200_OK)

# Rotate refresh tokens on use (optional)
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }
```

#### Permission Checks

```python
from rest_framework.permissions import BasePermission

class IsApprover(BasePermission):
    """Only allow if user is assigned as approver."""

    def has_object_permission(self, request, view, obj):
        # Check relationship, not role
        return request.user == obj.user.approver

class IsOwnProfileOrAdmin(BasePermission):
    """Only allow access to own profile or admin."""

    def has_object_permission(self, request, view, obj):
        return request.user == obj or request.user.is_staff

# Apply permissions
class LeaveRequestViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsApprover]
```

### Input Validation

#### Serializer Validation

```python
class LeaveRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveRequest
        fields = ['category', 'start_date', 'end_date', 'hours']

    def validate_hours(self, value):
        if value <= 0:
            raise serializers.ValidationError("Hours must be > 0")
        if value > 16:
            raise serializers.ValidationError("Hours must be <= 16")
        return value

    def validate(self, attrs):
        if attrs['end_date'] < attrs['start_date']:
            raise serializers.ValidationError("End date must be after start date")
        return attrs
```

#### Prevent SQL Injection

```python
# Good: ORM automatically escapes
users = User.objects.filter(email=user_input)

# Bad: Don't use string interpolation
users = User.objects.raw(f"SELECT * FROM users WHERE email = '{user_input}'")

# Good: Use parameterized queries if needed
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute(
        "SELECT * FROM users WHERE email = %s",
        [user_input]
    )
```

### Secrets Management

#### Environment Variables

```python
# Use environment variables, never hardcode secrets
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')
JWT_SECRET = os.getenv('JWT_SECRET_KEY')

# Validate required secrets
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable not set")
```

#### .env File Management

```bash
# .env.example (safe to commit)
DEBUG=False
SECRET_KEY=change-this-in-production
DATABASE_URL=postgresql://user:pass@localhost:5432/db

# .env (add to .gitignore)
DEBUG=False
SECRET_KEY=your-actual-secret-key
DATABASE_URL=postgresql://prod:actual_pass@prod_db:5432/db
```

### HTTPS & Secure Cookies

```python
# Production settings
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
```

### CORS Configuration

```python
# Good: Whitelist specific origins
CORS_ALLOWED_ORIGINS = [
    "https://example.com",
    "https://app.example.com",
]

# Development only
if DEBUG:
    CORS_ALLOWED_ORIGINS += [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

# Avoid: Allow all origins
CORS_ALLOW_ALL_ORIGINS = True  # NEVER in production
```

### Rate Limiting

```python
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

class AnonThrottle(AnonRateThrottle):
    scope = 'anon'
    THROTTLE_RATES = {'anon': '20/min'}

class UserThrottle(UserRateThrottle):
    scope = 'user'
    THROTTLE_RATES = {'user': '60/min'}

class LeaveRequestViewSet(viewsets.ModelViewSet):
    throttle_classes = [AnonThrottle, UserThrottle]
```

### Logging & Monitoring

#### Avoid Logging Secrets

```python
import logging

logger = logging.getLogger(__name__)

# Bad: Logs password
def login(email, password):
    logger.info(f"Login attempt: {email} {password}")

# Good: Only log necessary info
def login(email, password):
    logger.info(f"Login attempt for {email}")
    # Password not logged

# Log security events
def approve_leave(leave_id, approver):
    logger.warning(f"Leave {leave_id} approved by {approver}")
```

#### Audit Trail

```python
class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    action = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)
    changes = models.JSONField()  # Before/after state
    reason = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']

# Log all sensitive actions
def approve_leave(leave_id, approver_id, notes):
    leave = LeaveRequest.objects.get(id=leave_id)
    old_balance = leave.user.balance.hours

    leave.status = 'APPROVED'
    leave.approver_id = approver_id
    leave.save()

    # Log the action
    AuditLog.objects.create(
        user_id=approver_id,
        action='APPROVE_LEAVE',
        changes={
            'leave_id': leave_id,
            'old_balance': str(old_balance),
            'new_balance': str(leave.user.balance.hours),
        },
        reason=notes
    )
```

### Data Protection

#### Encryption (Future)

```python
from cryptography.fernet import Fernet

# For sensitive fields
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
cipher = Fernet(ENCRYPTION_KEY)

def encrypt_field(value):
    return cipher.encrypt(value.encode())

def decrypt_field(value):
    return cipher.decrypt(value).decode()
```

#### Data Retention

```python
from django.utils import timezone
from datetime import timedelta

# Delete old notifications
def cleanup_old_notifications():
    cutoff_date = timezone.now() - timedelta(days=30)
    Notification.objects.filter(created_at__lt=cutoff_date).delete()

# Keep audit logs for 7 years (compliance)
def cleanup_old_audit_logs():
    cutoff_date = timezone.now() - timedelta(days=365*7)
    AuditLog.objects.filter(timestamp__lt=cutoff_date).delete()
```

---

## Security Checklist

Before deploying to production:

- [ ] All secrets in environment variables
- [ ] HTTPS/SSL configured
- [ ] HSTS headers enabled
- [ ] Secure cookies configured (HttpOnly, Secure, SameSite)
- [ ] CORS origins whitelisted
- [ ] Rate limiting configured
- [ ] Input validation on all endpoints
- [ ] SQL injection tests passed
- [ ] XSS prevention implemented
- [ ] CSRF tokens validated
- [ ] Password hashing verified
- [ ] Secret rotation policy defined
- [ ] Audit logging implemented
- [ ] Error messages sanitized (no internal details)
- [ ] Dependencies scanned for vulnerabilities
- [ ] Security headers configured
- [ ] Penetration testing completed
- [ ] Disaster recovery plan documented
- [ ] Incident response plan ready
- [ ] Data backup strategy verified

---

## Performance Checklist

Before launch:

- [ ] API response time < 500ms (p99)
- [ ] Page load time < 3 seconds
- [ ] Database queries optimized (no N+1)
- [ ] Indexes created on frequently filtered fields
- [ ] Pagination implemented on all list endpoints
- [ ] Code splitting implemented (frontend)
- [ ] Bundle size < 300KB (gzipped)
- [ ] Caching strategy defined
- [ ] Load testing completed
- [ ] Database connection pooling configured
- [ ] CDN configured for static assets
- [ ] Monitoring and alerts set up

---

*Follow these guidelines to build secure, performant applications.*
